"""
script_patcher.py
=================
Módulo de post-procesado para inyectar parámetros de entrenamiento
seleccionados por el usuario en el script generado por la IA.

El LLM no siempre usa el mismo nombre de variable para los mismos
conceptos, por lo que este módulo cubre todos los alias conocidos
mediante patrones regex.
"""

import re
from typing import Optional

# Grupos de alias conocidos para cada parámetro.
# Se ordenan de más específico a más genérico para evitar falsos positivos.
_PARAM_ALIASES: dict[str, list[str]] = {
    "max_trials": [
        r"MAX_TRIALS",
        r"N_TRIALS",
        r"MAX_ITER",
        r"n_trials",
        r"max_iter",
        r"num_trials",
    ],
    "cv_folds": [
        r"CV_FOLDS",
        r"CV_TEST_SIZE",
        r"N_SPLITS",
        r"n_splits",
        r"cv_folds",
        r"num_folds",
        r"n_folds",
    ],
    "timeout": [
        r"OPTUNA_TIMEOUT",
        r"TIMEOUT_MINUTES",
        r"TIMEOUT_SECONDS",
        r"timeout_minutes",
        r"timeout_seconds",
        r"timeout",
    ],
}


def patch_training_params(
    script: str,
    max_trials: Optional[int] = None,
    cv_folds: Optional[int] = None,
    timeout_minutes: Optional[int] = None,
) -> tuple[str, dict[str, list[str]]]:
    """
    Inyecta los parámetros de entrenamiento elegidos por el usuario
    en el script generado por la IA, cubriendo todos los alias conocidos.

    Args:
        script:          El script Python generado por el LLM.
        max_trials:      Número máximo de trials de Optuna.
        cv_folds:        Número de folds/splits para la validación cruzada.
        timeout_minutes: Tiempo máximo de optimización en minutos.

    Returns:
        Tupla (script_parcheado, cambios_realizados) donde `cambios_realizados`
        es un dict con los nombres de variables que se han sustituido, útil
        para loguear/depurar.
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
            # Coincide con: NOMBRE_VAR = <número entero o decimal>
            # (?m) → multiline, ^ ancla al inicio de línea
            pattern = rf"(?m)^({alias})\s*=\s*[\d.]+"
            new_script, n_subs = re.subn(pattern, rf"\1 = {value}", script)
            if n_subs > 0:
                script = new_script
                applied[param].append(alias)

    return script, applied
