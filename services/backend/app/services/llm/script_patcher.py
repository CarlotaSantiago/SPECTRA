"""
script_patcher.py
=================
Modulo centralizado para:
  1. Extraer los parametros de entrenamiento reales del usuario (cv_folds, max_trials).
  2. Inyectar valores "light" en el payload antes de enviarlo al training service,
     de forma que el LLM genere un script rapido sin entrenamiento largo.
  3. Parchar el script generado por el LLM sustituyendo los valores de prueba
     por los valores reales que eligio el usuario.

El LLM no siempre usa el mismo nombre de variable para los mismos conceptos,
por lo que el patcher cubre todos los alias conocidos mediante patrones regex.
"""

import copy
import re
from typing import Any, Dict, Optional

# ─── Valores minimos inyectados para generacion rapida del script ────────────
LIGHT_CV_FOLDS = 2
LIGHT_MAX_TRIALS = 2

# Grupos de alias conocidos para cada parametro.
# Se ordenan de mas especifico a mas generico para evitar falsos positivos.
# Cubre variables de asignacion al inicio de linea: VAR = <numero>
_PARAM_ALIASES: dict[str, list[str]] = {
    "max_trials": [
        # Mayusculas (constantes al inicio de modulo)
        r"MAX_TRIALS",
        r"N_TRIALS",
        r"MAX_ITER",
        r"NUM_TRIALS",
        # Minusculas (variables locales dentro de funciones)
        r"max_trials",
        r"n_trials",
        r"max_iter",
        r"num_trials",
        r"n_iterations",
        r"num_iterations",
    ],
    "cv_folds": [
        # Mayusculas (constantes al inicio de modulo)
        r"CV_FOLDS",
        r"N_SPLITS",
        r"NUM_FOLDS",
        r"N_FOLDS",
        # Minusculas (variables locales dentro de funciones)
        r"cv_folds",
        r"n_splits",
        r"num_folds",
        r"n_folds",
        r"cv_splits",
    ],
    "timeout": [
        # Mayusculas (constantes al inicio de modulo)
        r"OPTUNA_TIMEOUT",
        r"TIMEOUT_MINUTES",
        r"TIMEOUT_SECONDS",
        r"TIMEOUT",
        # Minusculas (variables locales dentro de funciones)
        r"timeout_minutes",
        r"timeout_seconds",
        r"timeout",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE PAYLOAD
# ─────────────────────────────────────────────────────────────────────────────

def extract_user_training_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae los parametros reales de entrenamiento definidos por el usuario
    desde el campo 'dossier.user_constraints' del payload del frontend.

    Estructura esperada:
        dossier.user_constraints.cv_strategy.folds       -> cv_folds
        dossier.user_constraints.tuning_strategy.max_trials -> max_trials
        dossier.user_constraints.tuning_strategy.timeout   -> timeout_minutes

    Returns:
        Dict con claves cv_folds, max_trials, timeout_minutes.
        Devuelve None para los valores no presentes.
    """
    dossier = data.get("dossier", {})
    constraints = dossier.get("user_constraints", {})

    # cv_folds viene en: user_constraints.cv_strategy.folds
    cv_strategy = constraints.get("cv_strategy", {})
    cv_folds = cv_strategy.get("folds")

    # max_trials y timeout vienen en: user_constraints.tuning_strategy
    tuning = constraints.get("tuning_strategy", {})
    max_trials = tuning.get("max_trials")
    timeout_minutes = tuning.get("timeout")

    return {
        "cv_folds": int(cv_folds) if cv_folds is not None else None,
        "max_trials": int(max_trials) if max_trials is not None else None,
        "timeout_minutes": int(timeout_minutes) if timeout_minutes is not None else None,
    }


def inject_light_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea una copia profunda del payload e inyecta valores minimos en los
    parametros de entrenamiento para que el LLM genere un script rapido.

    Valores inyectados:
      - cv_folds   -> LIGHT_CV_FOLDS  (2)
      - max_trials -> LIGHT_MAX_TRIALS (2)

    El timeout NO se modifica: el LLM recibe el valor real del usuario.
    No modifica el objeto original.

    Returns:
        Nueva copia del payload con los valores light inyectados.
    """
    payload = copy.deepcopy(data)

    # Inyectamos en dossier.user_constraints para que el training service los lea
    dossier = payload.setdefault("dossier", {})
    constraints = dossier.setdefault("user_constraints", {})

    cv_strategy = constraints.setdefault("cv_strategy", {})
    cv_strategy["folds"] = LIGHT_CV_FOLDS

    tuning = constraints.setdefault("tuning_strategy", {})
    tuning["max_trials"] = LIGHT_MAX_TRIALS

    # Tambien inyectamos en global_metadata.search_config por si el
    # training service lo lee de ahi
    global_meta = dossier.setdefault("global_metadata", {})
    search_cfg = global_meta.setdefault("search_config", {})
    search_cfg["cv_folds"] = LIGHT_CV_FOLDS
    search_cfg["max_iter"] = LIGHT_MAX_TRIALS

    return payload


# ─────────────────────────────────────────────────────────────────────────────
# PATCHER DE SCRIPT
# ─────────────────────────────────────────────────────────────────────────────

def patch_training_params(
    script: str,
    max_trials: Optional[int] = None,
    cv_folds: Optional[int] = None,
    timeout_minutes: Optional[int] = None,
) -> tuple[str, dict[str, list[str]]]:
    """
    Inyecta los parametros de entrenamiento elegidos por el usuario
    en el script generado por la IA, cubriendo todos los alias conocidos.

    El timeout NO se parchea por defecto (pasar None para omitirlo).

    Args:
        script:          El script Python generado por el LLM.
        max_trials:      Numero maximo de trials de Optuna (None = no modificar).
        cv_folds:        Numero de folds/splits para validacion cruzada (None = no modificar).
        timeout_minutes: Tiempo maximo en minutos (None = no modificar).

    Returns:
        Tupla (script_parcheado, cambios_realizados) donde cambios_realizados
        es un dict con los nombres de variables sustituidos, util para debug.
    """
    patches: dict[str, Optional[str]] = {
        "max_trials": str(max_trials) if max_trials is not None else None,
        "cv_folds":   str(cv_folds)   if cv_folds   is not None else None,
        # El LLM mezcla minutos y segundos; normalizamos siempre a segundos
        "timeout":    str(timeout_minutes * 60) if timeout_minutes is not None else None,
    }

    applied: dict[str, list[str]] = {}

    for param, value in patches.items():
        if value is None:
            continue

        applied[param] = []

        for alias in _PARAM_ALIASES[param]:
            # Coincide con: NOMBRE_VAR = <numero entero o decimal>
            # (?m) -> multiline, ^ ancla al inicio de linea
            # Tambien captura sangria (indentacion) con \s* antes del nombre
            pattern = rf"(?m)^(\s*{alias})\s*=\s*[\d.]+"
            new_script, n_subs = re.subn(pattern, rf"\1 = {value}", script)
            if n_subs > 0:
                script = new_script
                applied[param].append(alias)

    return script, applied
