"""
model_router.py
===============
Módulo de routing inteligente para la Etapa 2 de SPECTRA.

Responsabilidades:
  1. Detectar la capacidad del modelo LLM consultando la API de Ollama.
  2. Enrutar a modo FULL (modelos ≥ 14B) o STAGED (modelos < 14B).
  3. En modo STAGED: generar el script en 3 llamadas secuenciales,
     validando y reparando cada fragmento antes de continuar.
  4. Self-healing mode-aware: en STAGED repara solo el fragmento fallido;
     en FULL repara el script completo.

Uso:
    from model_router import orchestrate_pipeline
    result = orchestrate_pipeline(toon_dossier, ollama_url, model_name)
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import textwrap
from typing import Literal

import requests


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

CAPABLE_THRESHOLD_B = 14          # parámetros mínimos (en miles de millones)
MAX_REPAIR_ATTEMPTS = 3
SANDBOX_TIMEOUT_S   = 900         # 15 min por ejecución

# Errores que indican problema de entorno, no del script generado
ENVIRONMENT_ERRORS = [
    "KeyboardInterrupt",
    "OSError: [Errno 28]",         # disco lleno
    "MemoryError",
    "CUDA out of memory",
    "SystemExit",
]

# Errores de dependencias no instaladas (se pueden resolver con pip)
DEPENDENCY_ERRORS = [
    "ModuleNotFoundError",
    "ImportError",
]


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — DETECCIÓN DE CAPACIDAD DEL MODELO
# ─────────────────────────────────────────────────────────────────────────────

def _parse_params_from_name(model_name: str) -> float | None:
    """
    Extrae el número de parámetros (en B) directamente del nombre del modelo.

    Estrategia: busca patrones del tipo '7b', '13b', '70b', '0.5b', '1.5b'
    en el nombre (case-insensitive). Devuelve None si no encuentra nada.

    Ejemplos:
        'qwen2.5:7b-coder'   → 7.0
        'llama3.1:70b-q4'    → 70.0
        'phi3:3.8b'          → 3.8
        'mixtral:8x7b'       → 56.0   (MoE: multiplica)
        'mistral:latest'     → None
    """
    name_lower = model_name.lower()

    # Caso MoE: patron NxMb (p.ej. 8x7b → 56B activos)
    moe = re.search(r"(\d+)x(\d+(?:\.\d+)?)b", name_lower)
    if moe:
        return float(moe.group(1)) * float(moe.group(2))

    # Caso estándar: Nb o N.Mb
    standard = re.search(r"(\d+(?:\.\d+)?)b", name_lower)
    if standard:
        return float(standard.group(1))

    return None


def _estimate_params_from_size(model_info: dict) -> float | None:
    """
    Estima el número de parámetros a partir del tamaño en bytes del modelo.

    Heurística: un modelo F16 usa ~2 bytes/param; Q4 ~0.5 bytes/param.
    Usamos 1.0 bytes/param como estimación conservadora (tiende a subestimar,
    lo que es seguro: preferimos clasificar un modelo como 'pequeño' antes
    que asumir que es capaz y que falle).

    Devuelve None si no hay información de tamaño disponible.
    """
    size_bytes = model_info.get("size")
    if not size_bytes:
        return None
    bytes_per_param = 1.0                      # estimación conservadora
    params_b = size_bytes / (bytes_per_param * 1e9)
    return round(params_b, 1)


def detect_model_capacity(ollama_url: str, model_name: str) -> dict:
    """
    Consulta la API de Ollama y determina si el modelo supera el threshold.

    Prioridad de detección:
      1. Parseo del nombre del modelo  (más fiable, sin ambigüedad).
      2. Estimación por tamaño en bytes (fallback si el nombre no tiene Nb).
      3. Clasificación conservadora como 'small' si ninguna fuente funciona.

    Devuelve un dict con:
        {
          'model_name':   str,
          'params_b':     float | None,   # parámetros en miles de millones
          'source':       str,            # 'name' | 'size' | 'unknown'
          'mode':         'full' | 'staged',
          'capable':      bool,
        }
    """
    try:
        resp = requests.post(
            f"{ollama_url}/api/show",
            json={"name": model_name},
            timeout=10,
        )
        resp.raise_for_status()
        model_info = resp.json()
    except Exception as exc:
        # Si no podemos consultar Ollama, modo conservador: staged
        return {
            "model_name": model_name,
            "params_b":   None,
            "source":     "unknown",
            "mode":       "staged",
            "capable":    False,
            "warning":    f"No se pudo consultar Ollama: {exc}",
        }

    # 1. Intentar por nombre
    params_b = _parse_params_from_name(model_name)
    source   = "name"

    # 2. Fallback: estimar por tamaño
    if params_b is None:
        params_b = _estimate_params_from_size(model_info)
        source   = "size" if params_b is not None else "unknown"

    # 3. Decisión
    if params_b is None:
        # No hay información: modo conservador
        capable = False
        mode    = "staged"
    else:
        capable = params_b >= CAPABLE_THRESHOLD_B
        mode    = "full" if capable else "staged"

    return {
        "model_name": model_name,
        "params_b":   params_b,
        "source":     source,
        "mode":       mode,
        "capable":    capable,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2 — CONSTRUCCIÓN DE PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

# ── 2a. Modo FULL ─────────────────────────────────────────────────────────────

FULL_SYSTEM_PROMPT = """\
You are the Master Pipeline Orchestrator, a Senior Lead Data Scientist.
Your goal is to generate a professional, high-performance, and IMMEDIATELY
EXECUTABLE Python script for model training.

DIVISION OF RESPONSIBILITIES:
The dossier already contains 'chain_strategy' with the structural pipeline
decision (ClassifierChain, RegressorChain, HybridChain, GatedChain,
MultiOutput). YOUR responsibility is to decide the MODELS and METRICS for
each target.

RESPONSIBILITIES:
1. DATA LOADING: Locate the '#LOCATION DATAFRAME' section in the dossier.
   Extract 'path' and 'extension_file'. Load using the correct pandas reader.
   Do NOT hardcode 'data.csv'.
2. MODEL PERSISTENCE: Save every model as './model/model_{target_name}.joblib'.
   Ensure the directory exists using os.makedirs(..., exist_ok=True).
3. Read 'chain_strategy.target_profiles' for each target:
   - subclass: NOMINAL or ORDINAL
   - n_classes: number of unique classes
   - mapping: ordinal encoding if applicable
   Select the most appropriate model and evaluation metric.
4. Implement the chain strategy exactly as specified. Do NOT change it.
5. GatedChain architecture rules:
   - Train the GATING MODEL only on rows where the gating target is NOT null.
   - Train each SPECIALIST MODEL only on the subset where gating_target == active_class.
   - ALWAYS use cross_val_predict() for out-of-fold predictions. NEVER call
     predict() or predict_proba() on the full training set.
6. Optuna objective function rules:
   - The objective(trial) function MUST call trial.suggest_int / suggest_float /
     suggest_categorical to sample hyperparameters.
   - Instantiate the model INSIDE the objective with the sampled params.
   - Return a scalar metric (float) from cross_val_score.
   - Call study.best_params ONLY after study.optimize() has finished.
7. Save each model as model_{target}.joblib and each preprocessor as
   preprocessor_stage{N}.joblib using joblib.
8. Print final summary: best params + validation metrics per target.

HYPERPARAMETER SEARCH SPACE RULES:
- Use DEFAULT_SEARCH_SPACES from the dossier as base.
- For optuna: use suggest_int / suggest_float / suggest_categorical.
  Example for LGBMClassifier:
      n_est = trial.suggest_int('n_estimators', 100, 500, step=100)
      lr    = trial.suggest_float('learning_rate', 0.01, 0.1, log=True)
      model = LGBMClassifier(n_estimators=n_est, learning_rate=lr)
      return cross_val_score(model, X, y, cv=cv, scoring='f1_macro').mean()
- Always respect timeout_minutes and cv_folds from search_config.
- Print param_space dict BEFORE starting the search.

CRITICAL CODING RULES:
- NEVER access model.best_params_ on a raw estimator.
- NEVER call predict() / predict_proba() on the full training set.
- ALWAYS import os and call os.makedirs('./model', exist_ok=True) at the top.
- ALWAYS include all necessary imports at the top of the script.

OUTPUT FORMAT:
1. A short "## Orchestration Reasoning" section (plain text, no code).
2. A single Python code block with all the code.
3. Nothing after the code block.
"""


def build_full_prompt(toon_dossier: str) -> str:
    return (
        f"Please orchestrate the training pipeline for the following dossier:\n\n"
        f"{toon_dossier}"
    )


# ── 2b. Modo STAGED — tres prompts focalizados ────────────────────────────────

STAGED_SYSTEM_PROMPT_BASE = """\
You are a Python expert. Generate ONLY the requested code fragment.
No explanations, no markdown prose outside the code block.
The fragment will be assembled with other fragments — write it as a
standalone function or block that can be imported.
ALWAYS include the necessary imports at the top of the fragment.
"""

def build_staged_prompt_1_gating(toon_dossier: dict) -> str:
    """
    Llamada 1: Solo el gating model + preprocesador de features.
    Contexto mínimo: metadata global + features + gating target.
    """
    gating      = toon_dossier.get("orchestration_plan", {}).get("gating_target", "")
    features    = list(toon_dossier.get("categorical_evaluation", {}).keys()) + \
                  list(toon_dossier.get("classified_evaluation",  {}).keys())
    search_cfg  = toon_dossier.get("global_metadata", {}).get("search_config", {})
    cv_folds    = search_cfg.get("cv_folds", 10)
    timeout     = search_cfg.get("timeout_minutes", 30)
    path        = toon_dossier.get("location", {}).get("path", "data.csv")
    ext         = toon_dossier.get("location", {}).get("extension_file", ".csv")

    # Perfiles de las features (solo lo necesario)
    cat_eval    = toon_dossier.get("categorical_evaluation", {})
    class_eval  = toon_dossier.get("classified_evaluation",  {})
    feature_profiles = {}
    for f in features:
        if f in cat_eval:
            print(f"Feature '{f}' is categorical with profile: {cat_eval[f]}")
            feature_profiles[f] = {
                "subclass": cat_eval[f].get("subclass"),
                "null_ratio": cat_eval[f].get("null_ratio", 0),
                "user_mandatory": cat_eval[f].get("user_mandatory", False),
            }
        elif f in class_eval:
            print(f"Feature '{f}' is classified with profile: {class_eval[f]}")
            feature_profiles[f] = {
                "subclass": class_eval[f].get("subclass"),
                "null_ratio": class_eval[f].get("null_ratio", 0),
                "user_mandatory": class_eval[f].get("user_mandatory", False),
            }

    gating_profile = toon_dossier.get("targets_evaluation", {}).get(gating, {})

    return textwrap.dedent(f"""\
        Generate a Python fragment that defines:

        1. `build_preprocessor(feature_profiles)` — returns a fitted
           ColumnTransformer that:
           - Applies OrdinalEncoder to NOMINAL/ORDINAL categorical features.
           - Applies StandardScaler to numeric features.
           - Passes through columns with user_mandatory=True unchanged if needed.
           - Handles null_ratio > 0 with SimpleImputer (strategy='most_frequent'
             for categoricals, 'median' for numerics).

        2. `build_gating_model(X_train, y_train, preprocessor, cv, timeout_minutes)`
           — trains a LGBMClassifier on the gating target using Optuna for
           hyperparameter tuning. Returns (fitted_pipeline, best_params, cv_score).
           - The Optuna objective MUST use trial.suggest_* inside the function.
           - Use cross_val_score inside the objective, NOT cross_val_predict.
           - After optimize(), access study.best_params.
           - Use StratifiedKFold(n_splits={cv_folds}).
           - Respect timeout_minutes={timeout}.

        CONTEXT:
        - Dataset path: '{path}', extension: '{ext}'
        - Gating target: '{gating}'
        - Gating target subclass: '{gating_profile.get("subclass", "NOMINAL")}'
        - Feature profiles: {feature_profiles}

        Output: ONLY a Python code block. No prose.
    """)


def build_staged_prompt_2_specialists(
    toon_dossier: dict,
    gating_target: str,
    dependent_targets: list[str],
) -> str:
    """
    Llamada 2: Un specialist model por cada target dependiente.
    Contexto mínimo: perfiles de los targets dependientes.
    """
    search_cfg = toon_dossier.get("global_metadata", {}).get("search_config", {})
    cv_folds   = search_cfg.get("cv_folds", 10)
    timeout    = search_cfg.get("timeout_minutes", 30)
    targets_ev = toon_dossier.get("targets_evaluation", {})

    target_profiles = {
        t: {
            "subclass":   targets_ev[t].get("subclass", "NOMINAL"),
            "n_classes":  targets_ev[t].get("n_classes", 2),
            "mapping":    targets_ev[t].get("mapping"),
            "priority_metrics": targets_ev[t].get("priority_metrics", ["F1-Score"]),
        }
        for t in dependent_targets
        if t in targets_ev
    }

    return textwrap.dedent(f"""\
        Generate a Python fragment that defines one function per specialist target.
        For each target in {dependent_targets}, define:

        `build_specialist_<TARGET>(X_subset, y_subset, preprocessor, cv, timeout_minutes)`

        Rules for each function:
        - Train ONLY on the subset of rows where the gating target ('{gating_target}')
          is active (i.e., rows that passed the gate).
        - Select model and metric based on subclass:
            NOMINAL  → LGBMClassifier, metric = 'roc_auc_ovr' or 'f1_macro'
            ORDINAL  → LGBMClassifier with ordinal encoding from mapping,
                       metric = cohen_kappa_score (linear weights)
        - Use Optuna for hyperparameter tuning. The objective MUST use
          trial.suggest_* inside the function body.
        - Use StratifiedKFold(n_splits={cv_folds}).
        - Respect timeout_minutes={timeout}.
        - Return (fitted_pipeline, best_params, cv_score).

        TARGET PROFILES:
        {target_profiles}

        Output: ONLY a Python code block. No prose.
    """)


def build_staged_prompt_3_assembly(
    toon_dossier: dict,
    fragment_1: str,
    fragment_2: str,
    gating_target: str,
    dependent_targets: list[str],
) -> str:
    """
    Llamada 3: Ensamblado final. Recibe los dos fragmentos ya validados
    y genera el script ejecutable completo.
    """
    path = toon_dossier.get("location", {}).get("path", "data.csv")
    ext  = toon_dossier.get("location", {}).get("extension_file", ".csv")

    return textwrap.dedent(f"""\
        You have two validated Python fragments. Assemble them into a single,
        immediately executable training script.

        FRAGMENT 1 (preprocessor + gating model):
        ```python
        {fragment_1}
        ```

        FRAGMENT 2 (specialist models):
        ```python
        {fragment_2}
        ```

        ASSEMBLY RULES:
        1. Load the dataset from '{path}' (extension '{ext}').
           Use pd.read_csv / pd.read_excel / pd.read_parquet accordingly.
        2. Call os.makedirs('./model', exist_ok=True) before saving.
        3. GatedChain execution order:
           a. Fit preprocessor on X_train features.
           b. Fit gating model on full X_train, y_train['{gating_target}'].
           c. For each dependent target in {dependent_targets}:
              - Get the subset mask where gating predictions are 'active'.
              - Fit the specialist model ONLY on that subset.
              - Use cross_val_predict() for out-of-fold predictions on the subset
                (NEVER call predict() on the full training set for chain features).
        4. Save each model:
           - './model/model_{gating_target}.joblib'
           {chr(10).join(f"           - './model/model_{t}.joblib'" for t in dependent_targets)}
           - './model/preprocessor_stage1.joblib'
        5. Print a final summary table with best_params and cv_score per target.
        6. All imports must be at the top of the script.
        7. Do NOT redefine the functions from the fragments — import or inline them.

        Output: ONLY a complete Python code block. No prose.
    """)


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3 — LLAMADAS AL LLM
# ─────────────────────────────────────────────────────────────────────────────

def _compute_num_ctx(
    payload_str: str,
    system_prompt: str,
    ollama_url: str,
    model_name: str,
    expected_output_tokens: int = 2048,
) -> int:
    """
    Calcula num_ctx seguro: mínimo entre lo necesario, el máximo
    arquitectural del modelo y lo que cabe en VRAM disponible.
    """
    # 1. Techo arquitectural
    try:
        info    = requests.post(f"{ollama_url}/api/show", json={"name": model_name}, timeout=10).json()
        max_ctx = info.get("model_info", {}).get("llama.context_length", 4096)
    except Exception:
        max_ctx = 4096

    # 2. Techo VRAM (solo GPU)
    try:
        ps        = requests.get(f"{ollama_url}/api/ps", timeout=5).json()
        vram_used = sum(m.get("size_vram", 0) for m in ps.get("models", []))
        smi       = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        vram_total_mb = int(smi.stdout.strip().split("\n")[0])
        vram_free     = vram_total_mb * 1024 * 1024 - vram_used
        ctx_per_vram  = int(vram_free * 0.8 / 200)
    except Exception:
        ctx_per_vram = max_ctx  # CPU-only: sin límite de VRAM

    # 3. Tokens necesarios
    input_tokens  = (len(payload_str) + len(system_prompt)) // 4
    needed        = input_tokens + expected_output_tokens
    rounded       = ((needed // 512) + 1) * 512

    return min(rounded, max_ctx, ctx_per_vram)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    ollama_url: str,
    model_name: str,
    temperature: float = 0.2,
    expected_output_tokens: int = 2048,
) -> str:
    """
    Llama al LLM vía Ollama y devuelve el contenido de texto de la respuesta.
    Lanza requests.HTTPError si la llamada falla.
    """
    num_ctx = _compute_num_ctx(
        user_prompt, system_prompt, ollama_url, model_name, expected_output_tokens
    )
    payload = {
        "model":   model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream":  False,
        "options": {"temperature": temperature, "num_ctx": num_ctx},
    }
    try:
        url = f"{ollama_url}/api/chat"
        print(f"LLM call to {model_name} with num_ctx={num_ctx} (estimated needed: {expected_output_tokens + len(user_prompt) // 4})")
        resp = requests.post(url, json=payload, timeout=600)
        print("LLM response received")
        resp.raise_for_status()
        response = resp.json()["message"]["content"]
        print(response)
        return response
    except Exception as e:
        print(f"Error crítico en la llamada al LLM: {e}")
        return f"ERROR_CONEXION_LLM: {e}"

def extract_code_block(llm_output: str) -> str:
    """
    Extrae el primer bloque ```python ... ``` de la salida del LLM.
    Si no hay bloque delimitado, devuelve el texto completo (fallback).
    """
    pattern = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
    match   = pattern.search(llm_output)
    return match.group(1).strip() if match else llm_output.strip()


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 4 — VALIDACIÓN Y SELF-HEALING
# ─────────────────────────────────────────────────────────────────────────────

def validate_syntax(code: str) -> tuple[bool, str]:
    """
    Comprueba que el código Python es sintácticamente válido con ast.parse().
    Devuelve (True, '') si es válido, (False, error_msg) si no.
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError en línea {e.lineno}: {e.msg}"


def validate_fragment_has_functions(code: str, required_names: list[str]) -> tuple[bool, str]:
    """
    Comprueba que el fragmento define todas las funciones requeridas.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, str(e)

    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = [name for name in required_names if name not in defined]
    if missing:
        return False, f"Funciones no encontradas en el fragmento: {missing}"
    return True, ""


def classify_error(stderr: str) -> Literal["environment", "dependency", "syntax", "shape", "structural"]:
    """
    Clasifica el error del stderr para guiar la estrategia de reparación.

    Categorías (en orden de prioridad de detección):
      environment  — KeyboardInterrupt, OOM, disco lleno: NO reintentar
      dependency   — ModuleNotFoundError, ImportError: añadir pip install
      syntax       — SyntaxError, IndentationError: corrección mínima
      shape        — errores de shape/dimensión: fix de transformación
      structural   — cualquier otro: puede reescribir el bloque afectado
    """
    if any(e in stderr for e in ENVIRONMENT_ERRORS):
        return "environment"
    if any(e in stderr for e in DEPENDENCY_ERRORS):
        return "dependency"
    if "SyntaxError" in stderr or "IndentationError" in stderr:
        return "syntax"
    if any(k in stderr for k in ["shape", "dimension", "mismatch", "reshape"]):
        return "shape"
    return "structural"


SELF_HEALING_SYSTEM_PROMPT = """\
You are a Senior Python Debugger. A generated script failed. Fix ONLY what the
error log points to. Preserve all architecture decisions (chain strategy, model
choices, metric choices, chain order).

REPAIR RULES:
1. environment errors  → DO NOT attempt repair. Return the token
                         UNRECOVERABLE_ERROR on the first line, then a one-line
                         explanation.
2. dependency errors   → Add 'import subprocess; subprocess.run([\"pip\", \"install\",
                         \"<package>\"], check=True)' at the top. Do NOT restructure.
3. syntax errors       → One-line fix only. Do NOT restructure anything else.
4. shape errors        → Fix the transformation causing the mismatch. Preserve models.
5. structural errors   → May rewrite the affected block. Preserve chain strategy,
                         model choices, and metric choices.

FORBIDDEN:
- NEVER replace cross_val_predict() with predict() on the full training set.
- NEVER remove joblib persistence blocks.
- NEVER change the chain strategy or execution order.

OUTPUT: Return ONLY the corrected Python code block. No apologies, no explanations
unless the fix is a critical architecture change.
"""


def build_repair_prompt(
    broken_code: str,
    stderr: str,
    error_type: str,
    attempt: int,
    context: str = "",
) -> str:
    """
    Construye el repair prompt para el LLM de reparación.
    En modo STAGED, 'context' contiene el fragmento específico que falló.
    """
    instructions = {
        "dependency": "Add a pip install call at the very top for the missing module. Do NOT change anything else.",
        "syntax":     "Fix ONLY the syntax error on the indicated line. One-line change maximum.",
        "shape":      "Fix the transformation causing the shape/dimension mismatch. Preserve model and metric choices.",
        "structural": "Rewrite the failing block. Preserve chain strategy, model choices, metric choices, and execution order.",
    }.get(error_type, "Fix what the error log points to.")

    return textwrap.dedent(f"""\
        ATTEMPT {attempt} of {MAX_REPAIR_ATTEMPTS}. Error type: {error_type}.

        INSTRUCTION: {instructions}

        ERROR LOG:
        {stderr}

        {"RELEVANT CONTEXT (fragment that failed):" + chr(10) + context if context else ""}

        BROKEN CODE:
        {broken_code}

        Return ONLY the corrected Python code block.
    """)


def run_in_sandbox(code: str, script_path: str = "spectra_generated.py") -> subprocess.CompletedProcess:
    """Escribe el script en disco y lo ejecuta en subproceso."""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True, text=True, timeout=SANDBOX_TIMEOUT_S,
        )
    except FileNotFoundError:
        # Fallback si en tu sistema el comando es obligatoriamente python3
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True, text=True, timeout=SANDBOX_TIMEOUT_S,
        )
    
    # Opcional: Limpiamos el archivo temporal tras usarlo para no llenar la carpeta de basura
    if os.path.exists(script_path):
        try:
            os.remove(script_path)
        except Exception:
            pass
            
    return result


def self_healing_loop(
    initial_code: str,
    ollama_url: str,
    model_name: str,
    context: str = "",
    label: str = "script",
) -> dict:
    """
    Bucle de auto-reparación genérico.

    Válido para un script completo (modo FULL) o un fragmento individual
    (modo STAGED). El parámetro 'context' es el fragmento específico en
    modo STAGED, vacío en modo FULL.

    Devuelve:
        {'status': 'success'|'failed'|'unrecoverable', 'code': str,
         'attempts': int, 'error': str}
    """
    current_code = initial_code

    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
        # Validación sintáctica rápida antes de ejecutar
        ok, syntax_err = validate_syntax(current_code)
        if not ok:
            # Tratar como error de sintaxis sin ejecutar
            error_type  = "syntax"
            stderr      = syntax_err
        else:
            result     = run_in_sandbox(current_code)
            if result.returncode == 0:
                return {
                    "status":   "success",
                    "code":     current_code,
                    "attempts": attempt,
                    "error":    "",
                }
            stderr     = result.stderr
            error_type = classify_error(stderr)

        print(f"  [{label}] Intento {attempt}/{MAX_REPAIR_ATTEMPTS} — error tipo '{error_type}'")

        # Errores de entorno: no reintentar
        if error_type == "environment":
            return {
                "status":   "unrecoverable",
                "code":     current_code,
                "attempts": attempt,
                "error":    stderr,
            }

        if attempt == MAX_REPAIR_ATTEMPTS:
            break

        # Pedir reparación al LLM
        repair_prompt = build_repair_prompt(
            broken_code=current_code,
            stderr=stderr,
            error_type=error_type,
            attempt=attempt,
            context=context,
        )
        raw_response = call_llm(
            system_prompt=SELF_HEALING_SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            ollama_url=ollama_url,
            model_name=model_name,
            temperature=0.1,
        )
        if raw_response.strip().startswith("UNRECOVERABLE_ERROR"):
            return {
                "status":   "unrecoverable",
                "code":     current_code,
                "attempts": attempt,
                "error":    raw_response,
            }
        current_code = extract_code_block(raw_response)

    return {
        "status":   "failed",
        "code":     current_code,
        "attempts": MAX_REPAIR_ATTEMPTS,
        "error":    stderr,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 5 — ORQUESTADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def _run_full_mode(
    toon_dossier: str,
    ollama_url: str,
    model_name: str,
) -> dict:
    """
    Modo FULL: una sola llamada al LLM con el TOON completo.
    Self-healing sobre el script completo.
    """
    print("[FULL] Generando script completo...")
    raw = call_llm(
        system_prompt=FULL_SYSTEM_PROMPT,
        user_prompt=build_full_prompt(toon_dossier),
        ollama_url=ollama_url,
        model_name=model_name,
        temperature=0.2,
        expected_output_tokens=3000,
    )
    initial_code = extract_code_block(raw)

    print("[FULL] Ejecutando y validando en sandbox...")
    result = self_healing_loop(
        initial_code=initial_code,
        ollama_url=ollama_url,
        model_name=model_name,
        label="FULL",
    )
    return result


def _run_staged_mode(
    toon_dossier: dict,
    ollama_url: str,
    model_name: str,
) -> dict:
    """
    Modo STAGED: tres llamadas focalizadas con validación entre cada una.
    Self-healing por fragmento antes de continuar al siguiente.
    """
    print("[STAGED] Detectando plan de orquestación en el dossier...")
    plan             = toon_dossier.get("orchestration_plan", {})
    print(f"Plan de orquestación detectado: {plan}")
    gating_target    = plan.get("gating", "")
    dependent_targets = plan.get("dependents", [])

    if not gating_target:
        return {
            "status": "failed",
            "code":   "",
            "attempts": 0,
            "error":  "orchestration_plan.gating_target está vacío en el TOON dossier.",
        }

    # ── Fragmento 1: preprocesador + gating model ──────────────────────────
    print("[STAGED] Llamada 1/3 — gating model...")
    raw_1 = call_llm(
        system_prompt=STAGED_SYSTEM_PROMPT_BASE,
        user_prompt=build_staged_prompt_1_gating(toon_dossier),
        ollama_url=ollama_url,
        model_name=model_name,
        temperature=0.15,
        expected_output_tokens=1500,
    )
    frag_1_initial = extract_code_block(raw_1)

    print("[STAGED] Validando fragmento 1...")
    result_1 = self_healing_loop(
        initial_code=frag_1_initial,
        ollama_url=ollama_url,
        model_name=model_name,
        context="Fragment 1: build_preprocessor + build_gating_model",
        label="STAGED-F1",
    )
    if result_1["status"] != "success":
        return {**result_1, "stage": "fragment_1"}

    # Verificar que las funciones requeridas están presentes
    ok, msg = validate_fragment_has_functions(
        result_1["code"], ["build_preprocessor", "build_gating_model"]
    )
    if not ok:
        return {"status": "failed", "code": result_1["code"],
                "attempts": result_1["attempts"], "error": msg, "stage": "fragment_1_missing_functions"}

    frag_1 = result_1["code"]

    # ── Fragmento 2: specialist models ────────────────────────────────────
    print("[STAGED] Llamada 2/3 — specialist models...")
    raw_2 = call_llm(
        system_prompt=STAGED_SYSTEM_PROMPT_BASE,
        user_prompt=build_staged_prompt_2_specialists(
            toon_dossier, gating_target, dependent_targets
        ),
        ollama_url=ollama_url,
        model_name=model_name,
        temperature=0.15,
        expected_output_tokens=1500,
    )
    frag_2_initial = extract_code_block(raw_2)

    print("[STAGED] Validando fragmento 2...")
    required_specialist_fns = [f"build_specialist_{t}" for t in dependent_targets]
    result_2 = self_healing_loop(
        initial_code=frag_2_initial,
        ollama_url=ollama_url,
        model_name=model_name,
        context=f"Fragment 2: specialist models for {dependent_targets}",
        label="STAGED-F2",
    )
    if result_2["status"] != "success":
        return {**result_2, "stage": "fragment_2"}

    ok, msg = validate_fragment_has_functions(result_2["code"], required_specialist_fns)
    if not ok:
        return {"status": "failed", "code": result_2["code"],
                "attempts": result_2["attempts"], "error": msg, "stage": "fragment_2_missing_functions"}

    frag_2 = result_2["code"]

    # ── Fragmento 3: ensamblado final ──────────────────────────────────────
    print("[STAGED] Llamada 3/3 — ensamblado final...")
    raw_3 = call_llm(
        system_prompt=STAGED_SYSTEM_PROMPT_BASE,
        user_prompt=build_staged_prompt_3_assembly(
            toon_dossier, frag_1, frag_2, gating_target, dependent_targets
        ),
        ollama_url=ollama_url,
        model_name=model_name,
        temperature=0.15,
        expected_output_tokens=2000,
    )
    frag_3_initial = extract_code_block(raw_3)

    print("[STAGED] Validando script ensamblado...")
    result_3 = self_healing_loop(
        initial_code=frag_3_initial,
        ollama_url=ollama_url,
        model_name=model_name,
        context="Fragment 3: final assembled script",
        label="STAGED-F3",
    )
    if result_3["status"] != "success":
        return {**result_3, "stage": "fragment_3"}

    return result_3


def orchestrate_pipeline(
    toon_dossier: dict | str,
    ollama_url: str,
    model_name: str,
) -> dict:
    """
    Punto de entrada principal de la Etapa 2.

    Detecta la capacidad del modelo y enruta a modo FULL o STAGED.

    Parámetros:
        toon_dossier : dict o str — el dossier completo de la Etapa 1.
                       Si es str, se usa tal cual para modo FULL.
                       Si es dict, se serializa a str para FULL y se usa
                       como dict para STAGED.
        ollama_url   : URL base de la API de Ollama (ej. 'http://localhost:11434')
        model_name   : nombre del modelo en Ollama (ej. 'qwen2.5:7b-coder')

    Devuelve:
        {
          'status':        'success' | 'failed' | 'unrecoverable',
          'mode':          'full' | 'staged',
          'model_info':    dict,   # resultado de detect_model_capacity
          'code':          str,    # script Python final
          'attempts':      int,
          'error':         str,
          'stage':         str,    # solo en modo staged si falla
        }
    """
    import json

    # Detectar capacidad
    model_info = detect_model_capacity(ollama_url, model_name)
    mode       = model_info["mode"]

    print(
        f"[ROUTER] Modelo: {model_name} | "
        f"Parámetros detectados: {model_info['params_b']}B "
        f"(fuente: {model_info['source']}) | "
        f"Modo: {mode.upper()}"
    )

    # Normalizar toon_dossier
    if isinstance(toon_dossier, dict):
        toon_str  = json.dumps(toon_dossier, ensure_ascii=False, indent=2)
        toon_dict = toon_dossier
    else:
        toon_str  = toon_dossier
        toon_dict = {}     # STAGED necesita dict; FULL solo necesita str

    # Enrutar
    if mode == "full":
        result = _run_full_mode(toon_str, ollama_url, model_name)
    else:
        if not toon_dict:
            # Si llegó como str, no podemos hacer STAGED correctamente
            print("[ROUTER] ADVERTENCIA: toon_dossier es str en modo STAGED. "
                  "Convirtiendo a FULL como fallback.")
            result = _run_full_mode(toon_str, ollama_url, model_name)
            mode   = "full_fallback"
        else:
            print("[ROUTER] Ejecutando en modo STAGED con llamadas focalizadas...")
            result = _run_staged_mode(toon_dict, ollama_url, model_name)

    return {**result, "mode": mode, "model_info": model_info}
