from importlib.resources import path
import io
import json
import logging
import os

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
from app.services.predict_models import predecir_final
from app.services.build_toon import build_toon_payload, integrar_analisis_llm
from app.services.strarified_sampling import stratified_sample_100
from app.services.orchestation import build_chain_strategy, compute_target_dependency_matrix
from app.services.train_models import entrenar_modelos_binarios, entrenar_modelos_prioridad

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
        for col in data.features:
            if col not in df.columns:
                logger.warning(f"Column not found: {col}")
                continue

            nombre = col + "_limpio"
            if nombre in df.columns:

                col = nombre

            series = df[col]

            col_data = classify_data(series, n_rows)

            col_data.update({
                "user_mandatory": col in data.mandatory,
                "unique_pool": series.dropna().astype(str).unique()[:20].tolist()
            })

            if col_data["technical_level"] in [1, 2]:
                columnas.append(col)

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
        semantic_analysis = call_ollama(data.model, system_prompt, user_prompt)
        with open("toon_dossier.json", "r", encoding="utf-8") as f:
            contenido = json.load(f)
        json_tecnico = integrar_analisis_llm(contenido, semantic_analysis)
        json_tecnico.update(dossier)

        df_for_matrix = df.sample(n=min(10000, len(df)), random_state=42) if len(df) > 0 else df
        matriz = compute_target_dependency_matrix(df_for_matrix, data.targets, json_tecnico["targets_evaluation"])
        orquestation = build_chain_strategy(matriz, json_tecnico["targets_evaluation"], threshold=0.15)
        matrix_dict = matriz.to_dict(orient='index')
        json_tecnico["target_dependency_matrix"] = matrix_dict
        json_tecnico["orchestration_plan"] = {
            "strategy": orquestation['strategy'],
            "order": orquestation['order'],
            "max_dependency": orquestation['max_dependency']
        }
        with open("toon_dossier.json", "w", encoding="utf-8") as f:
            json.dump(json_tecnico, f, indent=4, ensure_ascii=False)
        return {
            "status": "ok",
            "data": json_tecnico
        }

    except Exception as e:
        logger.error(f"process_state_1 failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }



@router.post("/process-state2")
def process_state_2(data: Dict[str, Any]):
    try:
        # Aquí procesaríamos la información de json_tecnico para entrenar modelos, etc.
        # Por ahora, solo devolvemos lo que recibimos para verificar la conexión.
        return {
            "status": "ok",
            "received_data": data
        }
    except Exception as e:
        logger.error(f"process_state_2 failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
class PredictionBlock(BaseModel):
    """
    Configuration block for a prediction section containing model selection and files to process.
    """
    active: bool
    models: List[str]
    files: List[str]

class PredictionRequest(BaseModel):
    """
    Request model for prediction endpoint containing MIO, HOMBRO, and PRIORIDAD blocks.
    """
    mio: PredictionBlock
    hombro: PredictionBlock
    prioridad: PredictionBlock


@router.post("/train")
async def run_training(data: PredictionRequest):
    """
    Run training models for MIO, HOMBRO, and PRIORIDAD blocks.
    
    Args:
        data: PredictionRequest containing model configuration for each block.
    
    Returns:
        Status and results of the training process.
    """
    resultados_globales = {}

    for nombre_bloque, bloque in [('mio', data.mio), ('hombro', data.hombro), ('prioridad', data.prioridad)]:
        if bloque.active:
            resultados_globales[nombre_bloque] = {}
            modelos_en_disco = os.listdir('./models')
            for model_key in bloque.models:
                nombre_modelo = f"{model_key}_{nombre_bloque}.pkl"
                if nombre_modelo not in modelos_en_disco:
                    if nombre_bloque == 'prioridad':
                        await entrenar_modelos_prioridad(bloque.files, model_key, nombre_bloque)
                        resultados_globales[nombre_bloque][model_key] = "entrenado_prioridad"
                    else:
                        await entrenar_modelos_binarios(bloque.files, model_key, nombre_bloque)
                        resultados_globales[nombre_bloque][model_key] = "entrenado"
                else:
                    resultados_globales[nombre_bloque][model_key] = "ya existente"

    if not resultados_globales:
        return {"status": "warning", "message": "No se seleccionó ningún bloque para entrenamiento."}

    return {"status": "success", "data": resultados_globales}


@router.post("/predict")
async def run_prediction(
    data: PredictionRequest):
    """
    Run prediction models for MIO, HOMBRO, and PRIORIDAD blocks.
    """
    resultados_globales = {}

    if data.mio.active:
        resultados_globales["mio"] = await procesar_bloque("MIO", data.mio, "mio")
    if data.hombro.active:
        resultados_globales["hombro"] = await procesar_bloque("HOMBRO", data.hombro, "hombro")
    if data.prioridad.active:
        resultados_globales["prioridad"] = await procesar_bloque("PRIORIDAD", data.prioridad, "prioridad")

    print(f"Resultados globales de predicción: {resultados_globales}")  # Esto te ayudará a ver qué se ha procesado
    # Validación: Si no se activó NADA, avisamos al usuario
    if not resultados_globales:
        return {
            "status": "warning", 
            "message": "No se seleccionó ningún bloque para análisis."
        }

    return {
        "status": "success",
        "data": resultados_globales
    }


async def procesar_bloque(nombre_bloque: str, config: PredictionBlock, target_col: str):
    """
    Process a prediction block by checking if models exist and running predictions.

    Args:
        nombre_bloque: Name of the block (e.g., "MIO", "HOMBRO", "PRIORIDAD").
        config: PredictionBlock containing model configuration and files to process.
        target_col: Target column name for the model (e.g., "etiqueta_mio").

    Returns:
        Dictionary with prediction results for each model.
    """
    resultados_bloque = {}
    modelos_en_disco = os.listdir('./models')

    for model_key in config.models:
        if nombre_bloque == 'PRIORIDAD':
            # La prioridad usa C1 y C2, comprobamos que al menos esté el C1
            nombre_archivo_modelo = f"{model_key}_{target_col}_C1.pkl"
        else:
            # Mio y Hombro son directos
            nombre_archivo_modelo = f"{model_key}_{target_col}.pkl"
        if nombre_archivo_modelo not in modelos_en_disco:
            if nombre_bloque == 'PRIORIDAD':
                print(f"Modelo {nombre_archivo_modelo} no encontrado, entrenando modelos de prioridad...")
                await entrenar_modelos_prioridad(config.files, model_key, target_col)
            else:
                print(f"Modelo {nombre_archivo_modelo} no encontrado, entrenando...")
                await entrenar_modelos_binarios(config.files, model_key, target_col)
        print(f"Ejecutando predicción para {model_key} en bloque {nombre_bloque}...")
        res = await predecir_final(model_key, config.files, target_col)
        resultados_bloque[model_key] = res
    
    return resultados_bloque