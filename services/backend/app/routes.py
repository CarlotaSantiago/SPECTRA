from importlib.resources import path
import io
import json
import logging
import os
import subprocess

import numpy as np
import pandas as pd
import torch
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pandas.api.types import is_float_dtype, is_numeric_dtype, is_object_dtype, is_string_dtype
from pydantic import BaseModel
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder
from typing import Any, Dict, List

from app.services.classify import classify_data, compute_information_gain, encode_series
from app.services.device_detection import get_device
from app.services.routeOllama import call_ollama
from app.services.processor import limpiar_datos
from app.services.build_toon import build_toon_payload, build_toon_s2, integrar_analisis_llm
from app.services.strarified_sampling import stratified_sample_100
from app.services.orchestation import build_chain_strategy, compute_target_dependency_matrix
from app.services.resolve_search import resolve_search_strategy, DEFAULT_SEARCH_SPACES

logger = logging.getLogger(__name__)


# 1. Usamos el APIRouter()
router = APIRouter()

@router.post("/upload") # 2. Cambiamos 'app.post' por 'router.post'
async def handle_upload(
    file: UploadFile = File(...),
    preprocess: bool = Form(...)
):
    """
    Handle file upload and preprocessing.
    
    Args:
        file: one file for preprocessing.
        indices_to_preprocess: JSON string containing indices of files to preprocess.
    
    Returns:
        Status and results of the upload and preprocessing.
    """
    try: 
        content = await file.read()

        if file.filename.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(io.BytesIO(content))
        else:
            # Añadimos soporte para CSV por si acaso
            data = pd.read_csv(io.BytesIO(content))

        if preprocess:
            columnas_a_limpiar = ['datosclini', 'sospechadiag']
            for col in columnas_a_limpiar:
                if col in data.columns:
                    data[f'{col}_limpio'] = limpiar_datos(data[col])

        n_rows = len(data)
        final_columns = data.columns.tolist()

        if preprocess:
            save_path = os.path.join("uploads", f"procesado_{file.filename}")
            data.to_excel(save_path, index=False)
        else:
            save_path = os.path.join("uploads", file.filename)
            data.to_excel(save_path, index=False)

        # Limpiar valores problemáticos para JSON
        data.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Convertir NaN a None (compatible con JSON)
        preview = data.head(10).replace({np.nan: None}).to_dict(orient='records')

        return {
            "status": "ok", 
            "n_rows": n_rows,
            "columnas": final_columns,
            "preview": preview,
            "path": save_path
        }
    except Exception as e:
        logger.error(f"Error en upload: {e}")

        return {
            "status": "error",
            "message": str(e)
        }
    
@router.get("/get-page")
def get_page(path: str, page: int = 1, size: int =150, filters: str = "{}"):
    try:
        if path.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(path)
        else:
            data = pd.read_csv(path)
        
        try:
            filter_dict = json.loads(filters)
            for col, value in filter_dict.items(): # <--- AQUÍ ESTABA EL ERROR
                if value and col in data.columns:
                    data = data[data[col].astype(str).str.contains(str(value), case=False, na=False)]
        except Exception as f_err:
            print(f"Error parseando filtros: {f_err}")
            # Si los filtros fallan, seguimos adelante con la data original
        
        n_rows = len(data)

        start = (page -1) * size
        end = start + size

        data_page = data.iloc[start:end].replace({np.nan: None, np.inf: None, -np.inf: None})

        return {
            "status": "ok",
            "items": data_page.to_dict(orient='records'),
            "n_rows": n_rows,
            "page": page,
            "size": size
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


class Dossier(BaseModel):
    """Model representing a dossier with total count, 
    path, features, targets, and mandatory fields."""
    n_rows: int
    path: str
    features: List[str]
    targets: List[str]
    mandatory: List[str]
    model: str

@router.post("/process-state1")
def process_state_1(data: Dossier):
    try:
        # 1. Carga de datos (Soporte para Excel y CSV con manejo de encoding)
        
        device = get_device()
        print(f"TRABAJANDO CON: {device}")

        df = pd.read_excel(data.path)
        df = df.fillna("")
        if df.empty:
            raise ValueError("Dataset is empty")
        
        if not data.targets:
            raise ValueError("No targets provided")
        
        n_rows = data.n_rows

        target_meta = {
            target: classify_data(df[target], n_rows)
            for target in data.targets
            if target in df.columns
        }
        columnas = list(data.targets)
        analysis_results = {}
        dossier = {
            "classified_evaluation": {}
        }
        columnas_limpias = {}
        for col in data.features:
            if col not in df.columns:
                logger.warning(f"Column not found: {col}")
                continue


            series = df[col]

            col_data = classify_data(series, n_rows)

            col_data.update({
                "user_mandatory": col in data.mandatory,
                "unique_pool": series.dropna().astype(str).unique()[:20].tolist()
            })

            if col_data["technical_level"] in [1, 2]:
                columnas.append(col)
                columnas_limpias[col] = df[col]
            else:
                columnas_limpias[col] = limpiar_datos(df[col])


            is_discrete = col_data["technical_level"] in [1, 2]

            col_data["information_gain"] = compute_information_gain(
                df,
                col,
                data.targets,
                target_meta,
                is_discrete,
                device=device
            )
            analysis_results[col] = col_data
            if col_data["technical_level"] in [1, 3, 4]:
                dossier["classified_evaluation"][col] = col_data

        save_path = os.path.join("uploads", "datos_limpios.xlsx")
        new_data = pd.DataFrame(columnas_limpias)
        for target in data.targets:
            if target in df.columns:
                new_data[target] = df[target]
        new_data.to_excel(save_path, index=False)
        sample_df = stratified_sample_100(df[columnas], data.targets)
        sample_df_clean = sample_df.astype(object).fillna("")
        metadata ={
            "n_rows": n_rows, 
            "targets": data.targets
        }

        print("Modelo: " + data.model)
        system_prompt = """/nothink
            You are a Data Science Assistant specialized in semantic feature classification.
            Your ONLY task: classify each feature in CATEGORICAL_SUBCLASS_EVALUATION and each target in TARGETS_SUBCLASS_EVALUATION as NOMINAL or ORDINAL.

            OUTPUT FORMAT — reproduce this structure exactly, one entry per feature:
            # SEMANTIC_CLASSIFICATION_RESULTS
            feature_name:
            subclass: NOMINAL
            mapping: null
            reasoning: one sentence.

            feature_name:
            subclass: ORDINAL
            mapping: {value1: 0, value2: 1, value3: 2}
            reasoning: one sentence.

            # TARGETS_SUBCLASS_EVALUATION
            target_name:
            subclass: NOMINAL
            mapping: null
            reasoning: one sentence.

            target_name:
            subclass: ORDINAL
            mapping: {value1: 0, value2: 1, value3: 2}
            reasoning: one sentence.

            CLASSIFICATION RULES:
            1. ORDINAL: values have a natural, unambiguous order or hierarchy (e.g. Junior < Senior, Baja < Alta).
            2. NOMINAL: values are distinct categories with no inherent order (e.g. departments, service codes).
            3. Use representative_sample to observe how values relate to targets before deciding.
            4. If uncertain between ORDINAL and NOMINAL, default to NOMINAL.
            5. For ORDINAL, mapping must include ALL values from unique_pool, starting at 0.
            6. For NOMINAL, mapping must be null.

            STRICT OUTPUT RULES:
            - Output ONLY the # SEMANTIC_CLASSIFICATION_RESULTS and # TARGETS_SUBCLASS_EVALUATION blocks.
            - No explanations outside the reasoning field.
            - No recommendations, no observations, no markdown headers beyond the block.
            - No bullet points, no numbered lists.
            - One entry per feature and target, in the same order as CATEGORICAL_SUBCLASS_EVALUATION and TARGETS_SUBCLASS_EVALUATION.
            """

        toon = build_toon_payload(metadata, analysis_results, sample_df_clean, data.features, target_meta)
        user_prompt = toon
        with open("toon_dossier.txt", "w", encoding="utf-8") as f:
            f.write(user_prompt)
        semantic_analysis = call_ollama(data.model, system_prompt, user_prompt, state=1)
        with open("toon_dossier.json", "r", encoding="utf-8") as f:
            contenido = json.load(f)
        json_tecnico = integrar_analisis_llm(contenido, semantic_analysis)
        json_tecnico.update(dossier)
        df_for_matrix = df.sample(n=min(10000, len(df)), random_state=42) if len(df) > 0 else df
        matriz = compute_target_dependency_matrix(df_for_matrix, data.targets, json_tecnico["targets_evaluation"])
        threshold_config = getattr(data, 'threshold_cfg', 'auto')
        orquestation = build_chain_strategy(df, matriz, json_tecnico["targets_evaluation"], threshold_config, json_tecnico)
        matrix_dict = matriz.to_dict(orient='index')
        json_tecnico["target_dependency_matrix"] = matrix_dict
        max_dep = float(matriz.where(matriz < 1.0).max().max())
        json_tecnico["orchestration_plan"] = {
            "strategy": orquestation['strategy'],
            "order": orquestation['order'] if orquestation.get('order') is not None else [],
            "max_dependency": max_dep
        }
        with open("toon_dossier.json", "w", encoding="utf-8") as f:
            json.dump(json_tecnico, f, indent=4, ensure_ascii=False)
        return {
            "status": "ok",
            "path": save_path,
            "extension": os.path.splitext(save_path)[1],
            "data": json_tecnico
        }

    except Exception as e:
        logger.error(f"process_state_1 failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }



# --- CONFIGURACIÓN DE REPARACIÓN ---
MAX_ATTEMPTS = 3
UNRECOVERABLE_ERRORS = ["MemoryError", "CUDA out of memory", "SystemExit", "OSError: [Errno 28]"]

def _docker_available() -> bool: 
    """
    Detecta automáticamente si Docker está instalado y en ejecución en el host.
    """
    try: 
        r = subprocess.run(['docker', 'info'], capture_output=True, timeout=5) 
        return r.returncode == 0 
    except (FileNotFoundError, subprocess.TimeoutExpired): 
        return False 

def _run_in_subprocess(code: str) -> subprocess.CompletedProcess: 
    """
    Ejecución clásica mediante un subproceso local de Python.
    """
    filename = "temp_execution_script.py"
    with open(filename, 'w', encoding='utf-8') as f: 
        f.write(code) 
    return subprocess.run( 
        ['python', filename], 
        capture_output=True, text=True, timeout=900 
    ) 

def _run_in_docker(code: str, dataset_path: str, output_path: str) -> subprocess.CompletedProcess: 
    """
    Ejecución en un entorno 100% aislado dentro de un contenedor Docker.
    Monta los volúmenes en modo lectura para datos y escritura para salidas.
    """
    filename = "/tmp/script_automl.py"
    with open(filename, 'w', encoding='utf-8') as f: 
        f.write(code) 
    
    cmd = [ 
        'docker', 'run', '--rm', 
        '-v', f'{dataset_path}:/data:ro',           # dataset en modo sólo lectura (read-only)
        '-v', f'{output_path}:/output',             # carpeta de salida para artefactos (.joblib)
        '-v', f'{filename}:/app/run.py',            # mapeo del script generado
        'python:3.11-slim', 
        'bash', '-c', 
        'pip install -q scikit-learn lightgbm xgboost joblib optuna pandas openpyxl pyarrow && python /app/run.py' 
    ] 
    return subprocess.run(cmd, capture_output=True, text=True, timeout=960) 

def run_script_in_sandbox(script_content: str, dataset_path: str, output_path: str, manifest: dict) -> subprocess.CompletedProcess: 
    """
    Determina de manera inteligente y según el manifest cómo ejecutar el código.
    """
    # Leer el modo deseado del manifest. Si no se indica o es 'auto', se auto-detecta.
    mode = manifest.get('execution_mode', 'auto')
    
    if mode == 'auto':
        use_docker = _docker_available()
    elif mode == 'docker':
        if not _docker_available():
            # Forzamos docker pero no está disponible: levantamos un proceso ficticio con el error
            res = subprocess.CompletedProcess(args=[], returncode=1)
            res.stderr = "Error: Docker mode forced in manifest but Docker is not available or running."
            return res
        use_docker = True
    else:  # 'subprocess'
        use_docker = False

    if use_docker: 
        return _run_in_docker(script_content, dataset_path, output_path) 
    return _run_in_subprocess(script_content) 

def classify_error(stderr: str) -> str:     
    """
    Clasifica el error para orientar de forma precisa la estrategia del LLM.
    """
    if 'SyntaxError' in stderr or 'IndentationError' in stderr: 
        return 'syntax'    
    if 'ModuleNotFoundError' in stderr or 'ImportError' in stderr: 
        return 'import'  
    if any(k in stderr for k in ['shape', 'dimension', 'mismatch']): 
        return 'shape'     
    return 'structural'  

def build_repair_prompt(dossier, broken_code, stderr, attempt, error_type) -> str:     
    """
    Construye un prompt de reparación parametrizado, indicando el tipo de error e intento actual.
    """
    return f'''  
    ATTEMPT {attempt} of {MAX_ATTEMPTS}. Error type: {error_type}.  
    ERROR LOG: {stderr} 
    ORIGINAL CODE: {broken_code}  
    ORIGINAL DOSSIER: {dossier}  
    
    Fix ONLY what the error log points to.  
    Preserve chain strategy, model choices, and metric choices.  
    Return ONLY the corrected Python code block. '''

@router.post("/process-state2")
def process_state_2(data: Dict[str, Any]):
    try:
        dossier = data["dossier"]
        model = data["model"]

        # Extraemos rutas por defecto o del dossier/manifest para Docker
        # Si no se definen en el input, asignamos valores por defecto locales seguros
        manifest = data.get("manifest", dossier.get("global_metadata", {}).get("manifest", {"execution_mode": "auto"}))
        dataset_path = data['path'] 
        output_path = data.get("output_path", "./output")
        # =========================================================================
        # INYECCIÓN DEL PASO 3: ESPACIOS DE BÚSQUEDA Y HEURÍSTICA DE ESTRATEGIA ("auto")
        # =========================================================================
        # 1. Resolvemos la estrategia real (grid, random, optuna) basándonos en el dossier
        search_resolution = resolve_search_strategy(dossier)
        
        # 2. Aseguramos que la estructura interna exista para no arrojar KeyError
        if "global_metadata" not in dossier:
            dossier["global_metadata"] = {}
        if "search_config" not in dossier["global_metadata"]:
            dossier["global_metadata"]["search_config"] = {
                "max_iter": 50, "max_combinations": 200, "cv_folds": 10, "timeout_minutes": 30
            }
            
        # 3. Mutamos la propiedad 'search_strategy' de "auto" a la seleccionada estadísticamente
        dossier["global_metadata"]["search_config"]["search_strategy"] = search_resolution["selected_strategy"]
        dossier["global_metadata"]["search_config"]["resolution_reasoning"] = search_resolution["reasoning"]
        
        # 4. Adjuntamos los espacios de búsqueda base estructurados para que Ollama sepa los rangos exactos
        dossier["base_hyperparameter_spaces"] = DEFAULT_SEARCH_SPACES
        # =========================================================================
        orchestrator_system_prompt = """ 
            You are the Master Pipeline Orchestrator, a Senior Lead Data Scientist.  
            
            Your goal is to generate a professional, high-performance, and IMMEDIATELY 
            EXECUTABLE Python script for model training. 
            
            DIVISION OF RESPONSIBILITIES:     
            The dossier already contains 'chain_strategy' with the structural pipeline    
            decision (ClassifierChain, RegressorChain, HybridChain, GatedChain, 
            MultiOutput).    YOUR responsibility is to decide the MODELS and METRICS for 
            each target. 
            
            RESPONSIBILITIES:       
            1. DATA LOADING: Locate the '#LOCATION DATAFRAME' section in the user prompt/dossier.
               Extract the specified 'path' and 'extension_file'. Your generated script MUST 
               load the dataset dynamically utilizing the correct pandas reader function corresponding 
               to that extension (e.g., pd.read_csv for csv, pd.read_excel for xlsx, pd.read_parquet for parquet).
               Do NOT hardcode 'data.csv' if the dossier specifies another target path or format.
            2. Read 'chain_strategy.target_profiles' for each target:          
                - subclass: NOMINAL or ORDINAL          
                - n_classes: number of unique classes          
                - mapping: ordinal encoding if applicable          
                Select the most appropriate model and evaluation metric based on these 
            facts.       
            3. Implement the chain strategy exactly as specified in 
            'chain_strategy.strategy'.          
                Do NOT change the strategy or execution order.       
            4. HybridChain / GatedChain: ALWAYS use cross_val_predict() —          
                NEVER call predict() or predict_proba() on the full training set.         
            5. Use the search_type specified in the dossier for hyperparameter tuning.      
            6. Save each model as model_{target}.joblib using joblib.       
            7. Print final summary with best params and validation metrics.     
            
            HYPERPARAMETER SEARCH SPACE RULES: 
            1. If the model EXISTS in DEFAULT_SEARCH_SPACES, use it as base. You may adjust 
            ranges based on TOON context, but always respect: 
            - grid search : total combinations <= search_budget.max_combinations 
            - random search: use scipy.stats distributions, not discrete lists 
            - optuna : define suggest_int / suggest_float / suggest_categorical  
            2. If the model does NOT exist in DEFAULT_SEARCH_SPACES:  
            a. Include ONLY the 3-5 most impactful hyperparameters for that model.  
                Prioritize: complexity control, regularization, learning rate.  
            b. Use no more than 3 values per hyperparameter.  
            c. Verify parameter names against the sklearn-compatible API.  
            d. Add a comment next to each parameter explaining why it was  
                included.  
            3. If search_strategy is "auto", select method using: 
            - n_features < 20 AND n_rows < 50k → grid 
            - n_features >= 20 OR n_rows >= 50k → random 
            - n_targets > 1 OR GatedChain → optuna  
            4. Always respect search_config, timeout_minutes and cv_folds.  
            5. Print param_space as a dict BEFORE the search starts.  
            This makes the search space auditable in the execution log.  
            Example: print("param_space:", param_space) 
            
            OUTPUT RULES: - Provide a brief "Orchestration Reasoning" section. - Provide the Python Code block.  - Do not include any conversational text after the code. - Ensure all necessary imports (pandas, sklearn, joblib, etc.) are at the top of 
            the generated script. 
            - Model Persistence: The script MUST include a final block using joblib to save:
            - Each trained model as 'model_{target_name}.joblib' (o '/output/model_{target_name}.joblib' si corre en Docker)
            - Each preprocessing transformer as 'preprocessor_stage{N}.joblib'
            """ 
        typo_correlation = dossier["orchestration_plan"]["strategy"]
        max_dependency = dossier["orchestration_plan"]["max_dependency"]
        dependency = "High" if (isinstance(max_dependency, (int, float)) and max_dependency > 0.15) else "Low"
        for target, info in dossier["targets_evaluation"].items():
            dependencies = dossier["target_dependency_matrix"][target]
            for dep_target, dep_value in dependencies.items():
                if dep_value > 0.15 and dep_target != target:
                    info["dependency"] = f"High (linked to {dep_target})"
                elif dep_target != target:
                    info["dependency"] = f"Low (linked to {dep_target})"
        toon = build_toon_s2(dossier, typo_correlation, max_dependency, dependency, dossier["targets_evaluation"], data)
        user_prompt = f"Please orchestrate the training pipeline for the following dossier:\n\n{toon}"
        orchestation_script = call_ollama(data["model"], orchestrator_system_prompt, user_prompt, state=2)
        if "```python" in orchestation_script:
            orchestation_script = orchestation_script.split("```python")[1].split("```")[0].strip()

        with open("orchestation_script.py", "w", encoding="utf-8") as f:
            f.write(orchestation_script) 

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"--- Intento de ejecución {attempt} ---")
            execution_result = run_script_in_sandbox(orchestation_script, dataset_path, output_path, manifest)

            if execution_result.returncode == 0:
                with open("orchestation_script.py", "a", encoding="utf-8") as f:
                    f.write(f"\n# --- EJECUCIÓN EXITOSA EN INTENTO {attempt}     ---\n")
                    f.write(execution_result.stdout)
                return {"status": "ok", "script": orchestation_script, "output": execution_result.stdout}
            
            # Si falla, comprobamos si es un error fatal (Memoria/Sistema)
            if any(err in execution_result.stderr for err in UNRECOVERABLE_ERRORS):
                return {
                    "status": "UNRECOVERABLE_ERROR",
                    "attempts": attempt,
                    "reason": "Hardware/System limits reached (OOM/Disk Full)."
                }
            if attempt == MAX_ATTEMPTS:
                break

            error_type = classify_error(execution_result.stderr)

            intento_instruccion = (
                "Fix ONLY what the error log explicitly points to with a minimal fix (e.g. one-line change/missing import)."
                if attempt == 1 
                else "You may rewrite structural or transformation blocks causing the mismatch, but preserve core model choices and chain order."
            )

            self_healing_system_prompt =  """ 
                You are the Master Pipeline Orchestrator in DEBUG MODE.  
                Your previous code failed, and you must now act as a Senior Debugger. 
                
                CONTEXT: 
                The original script was generated by an orchestrator that already 
                decided: 
                - The chain strategy (ClassifierChain, GatedChain, etc.) 
                - The model and metric for each target based on its subclass and 
                n_classes 
                - The hyperparameter search space and CV strategy 
                These decisions belong to the orchestrator, not to you. 
                Do NOT revisit or replace them unless the error log explicitly points to 
                them. 
                
                REPAIR RULES: 
                1. Fix ONLY what the error log points to. 
                    syntax / import errors → minimal one-line fix, no restructuring. 
                    shape / mismatch errors → fix the transformation causing the  
                                            mismatch. 
                    structural errors → may rewrite the affected block, but preserve 
                                    model choices, metric choices, and chain order. 
                2. Preserve model and metric choices: if the original script uses 
                    LGBMClassifier with kappa_linear for an ordinal target, keep it. 
                    Only replace a model if the error is caused by that specific model. 
                3. NEVER replace cross_val_predict() with predict() or predict_proba() 
                    on the full training set — this would introduce target leakage. 
                4. NEVER remove joblib persistence blocks. 
                5. On attempt 2+, you may rewrite larger blocks if the error is   
                    structural, but the chain strategy and execution order must remain    
                    identical. 
                
                UNRECOVERABLE ERRORS: 
                If the error is MemoryError, CUDA out of memory, SystemExit, or 
                OSError Errno 28 (disk full): return the token UNRECOVERABLE_ERROR 
                on the first line, followed by a one-line explanation. 
                
                OUTPUT: 
                Return ONLY the corrected Python code block. 
                No apologies, no explanations unless the fix is a critical    
                architecture change. 
                """
            repair_prompt = build_repair_prompt(dossier, orchestation_script, execution_result.stderr, attempt, error_type)
            orchestation_script = call_ollama(model, self_healing_system_prompt, repair_prompt, state=2)
            
            # Limpieza de formato para asegurar que solo tenemos código Python
            if "```python" in orchestation_script:
                orchestation_script = orchestation_script.split("```python")[1].split("```")[0].strip()
            with open("orchestation_script.py", "w", encoding="utf-8") as f:
                f.write(orchestation_script)
        return {
            "status": "failed",
            "last_error": execution_result.stderr
        }
    except Exception as e:
        logger.error(f"process_state_2 failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
