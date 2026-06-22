"""
Módulo que contiene la lógica de resolución heurística para determinar
la estrategia óptima de búsqueda de hiperparámetros (Grid, Random u Optuna).
"""

# -------------------------------------------------------------------------
# 1. ESPACIOS DE BÚSQUEDA POR DEFECTO (Según especificaciones de la pág 25)
# -------------------------------------------------------------------------
DEFAULT_SEARCH_SPACES = {
    # ── CLASIFICACIÓN ──
    "LGBMClassifier": {
        "n_estimators": [100, 300, 500],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7, -1],
        "subsample": [0.7, 0.85, 1.0],
        "num_leaves": [31, 63, 127],
    },
    "RandomForestClassifier": {
        "n_estimators": [100, 300, 500],
        "max_depth": [None, 5, 10, 20],
        "min_samples_split": [2, 5, 10],
        "max_features": ["sqrt", "log2"],
    },
    "XGBClassifier": {
        "n_estimators": [100, 300, 500],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7],
        "subsample": [0.7, 0.9, 1.0],
        "colsample_bytree": [0.7, 0.9, 1.0],
    },
    # ── REGRESIÓN ──
    "LGBMRegressor": {
        "n_estimators": [100, 300, 500],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7, -1],
        "subsample": [0.7, 0.85, 1.0],
        "num_leaves": [31, 63, 127],
    },
    "RandomForestRegressor": {
        "n_estimators": [100, 300, 500],
        "max_depth": [None, 5, 10, 20],
        "min_samples_split": [2, 5, 10],
        "max_features": ["sqrt", "log2", None],
    },
    "XGBRegressor": {
        "n_estimators": [100, 300, 500],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7],
        "subsample": [0.7, 0.9, 1.0],
        "colsample_bytree": [0.7, 0.9, 1.0],
    },
}

# -------------------------------------------------------------------------
# 2. MOTOR DE RESOLUCIÓN DE HEURÍSTICAS PARA STRATEGY = "auto"
# -------------------------------------------------------------------------
def resolve_search_strategy(toon_dossier: dict) -> dict:
    """
    Evalúa el contexto estadístico y estructural del TOON Dossier para inyectar
    las heurísticas de búsqueda automática requeridas por la documentación.
    """
    global_meta = toon_dossier.get("global_metadata", {})
    search_config = global_meta.get("search_config", {})

    # Extraemos la estrategia definida (puedes haberla fijado en Etapa 0 en el manifest)
    current_strategy = search_config.get("search_strategy", "auto")

    # Si el usuario forzó una estrategia explícitamente (grid, random, optuna), se preserva.
    if current_strategy != "auto":
        return {
            "selected_strategy": current_strategy,
            "reasoning": f"Estrategia forzada: '{current_strategy}'."
        }

    # --- Extracción de Métricas de Contexto Estadístico ---
    n_rows = global_meta.get("total_rows", 0)
    targets = global_meta.get("targets", [])
    n_targets = len(targets)

    # El número de features se deduce del bloque de evaluación categórica y numérica del TOON
    cat_eval = toon_dossier.get("categorical_subclass_evaluation", {})
    # Asumimos que también puedes tener un bloque numérico o sumamos las que no son targets
    n_features = len([k for k, v in cat_eval.items() if not v.get("is_target", False)])

    # Obtenemos la decisión estructural de la cadena resuelta previamente en la Etapa 2
    chain_strategy = toon_dossier.get("orchestration_plan", {}).get("strategy", "MultiOutput")

    # --- Aplicación Estricta de Heurísticas de Selección (Pág 25) ---
    complex_chains = ["GatedChain", "HybridChain", "ClassifierChain", "RegressorChain"]

    # Heurística 3: Complejidad de pipeline multipropósito o condicional
    if n_targets > 1 or chain_strategy in complex_chains:
        selected = "optuna"
        reasoning = (
            f"Pipeline complejo ({chain_strategy}) con {n_targets} targets. "
            "Se aplica optimización bayesiana con pruning (Optuna) para eficiencia."
        )

    # Heurística 2: Datasets con alta dimensionalidad o volumen de filas considerable
    elif n_features >= 20 or n_rows >= 50000:
        selected = "random"
        reasoning = (
            f"Espacio de búsqueda masivo (Features: {n_features}, Filas: {n_rows}). "
            "Se selecciona 'random' por eficiencia computacional."
        )

    # Heurística 1: Espacios de búsqueda pequeños y datasets contenidos
    elif n_features < 20 and n_rows < 50000:
        selected = "grid"
        reasoning = (
            f"Espacio acotado (Features: {n_features} < 20 AND Filas: {n_rows} < 50k). "
            "La exploración exhaustiva mediante 'grid search' es factible."
        )
    else:
        # Fallback de seguridad por defecto
        selected = "random"
        reasoning = "Parámetros fuera de rango estándar. Selección preventiva: 'random'."

    return {
        "selected_strategy": selected,
        "reasoning": reasoning,
        "context_evaluated": {
            "n_features": n_features,
            "n_rows": n_rows,
            "n_targets": n_targets,
            "chain_strategy": chain_strategy
        }
    }

# -------------------------------------------------------------------------
# 3. ENSAMBLADOR DEL ESPACIO DE BÚSQUEDA ADAPTADO PARA EL LLM ORQUESTADOR
# -------------------------------------------------------------------------
def get_search_payload_for_orchestrator(toon_dossier: dict) -> dict:
    """
    Modifica el sub-bloque search_config dentro del dossier para que el LLM
    orquestador de la Etapa 2.4 reciba las directrices exactas de límites y espacios.
    """
    strategy_resolution = resolve_search_strategy(toon_dossier)

    # Clonamos la configuración actual para actualizarla sin efectos secundarios colaterales
    updated_dossier = dict(toon_dossier)
    if "global_metadata" not in updated_dossier:
        updated_dossier["global_metadata"] = {}

    if "search_config" not in updated_dossier["global_metadata"]:
        updated_dossier["global_metadata"]["search_config"] = {
            "max_iter": 50,
            "max_combinations": 200,
            "cv_folds": 10,
            "timeout_minutes": 30
        }

    # Asignamos el valor calculado por la heurística sustituyendo el literal "auto"
    search_cfg = updated_dossier["global_metadata"]["search_config"]
    search_cfg["search_strategy"] = strategy_resolution["selected_strategy"]
    search_cfg["resolution_reasoning"] = strategy_resolution["reasoning"]

    # Adjuntamos el diccionario base para que el LLM conozca mallas iniciales y afine
    updated_dossier["base_hyperparameter_spaces"] = DEFAULT_SEARCH_SPACES

    return updated_dossier