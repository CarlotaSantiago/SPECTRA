from importlib.resources import path
import io
import json
import logging
import os

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pandas.api.types import is_float_dtype, is_numeric_dtype, is_object_dtype, is_string_dtype
from pydantic import BaseModel
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder
from typing import Any, Dict, List

from app.services.routeOllama import call_ollama
from app.services.processor import limpiar_datos
from app.services.predict_models import predecir_final
from app.services.build_toon import build_toon_payload
from app.services.strarified_sampling import stratified_sample_100
from app.services.train_models import entrenar_modelos_binarios, entrenar_modelos_prioridad

logger = logging.getLogger(__name__)


# 1. Usamos el APIRouter()
router = APIRouter()

@router.post("/upload") # 2. Cambiamos 'app.post' por 'router.post'
async def handle_upload(
    files: List[UploadFile] = File(...),
    indices_to_preprocess: str = Form(...) # Recibimos como str para evitar errores 422
):
    """
    Handle file upload and preprocessing.
    
    Args:
        files: List of uploaded files.
        indices_to_preprocess: JSON string containing indices of files to preprocess.
    
    Returns:
        Status and results of the upload and preprocessing.
    """
    try:
        # Convertimos el string JSON a lista de índices
        to_process_list = json.loads(indices_to_preprocess)
    except (json.JSONDecodeError, ValueError):
        # Si no es un JSON válido, asumimos que no se preprocesará nada
        to_process_list = []

    lista_dataframes = []

    for index, file in enumerate(files):
        content = await file.read()
        # Leer archivo actual
        df_temp = pd.read_excel(io.BytesIO(content)) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(content))

        # Aplicar limpieza si toca (tus funciones de stopwords)
        if index in to_process_list:
            columnas_a_limpiar = ['datosclini', 'sospechadiag']
            for col in columnas_a_limpiar:
                if col in df_temp.columns:
                    df_temp[f'{col}_limpio'] = limpiar_datos(df_temp[col])
        
        lista_dataframes.append(df_temp)

    # --- UNIFICACIÓN (Paso clave para Etapa 0) ---
    df_unificado = pd.concat(lista_dataframes, ignore_index=True)

    n_rows = len(df_unificado) # Número total de filas en el DataFrame unificado
    columnas_finales = df_unificado.columns.tolist() # Lista de columnas finales

    path_unificado = os.path.join("uploads", "dataset_unificado.xlsx")
    df_unificado.to_excel(path_unificado, index=False)

    # Limpiar valores problemáticos para JSON
    df_unificado.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Convertir NaN a None (compatible con JSON)
    preview = df_unificado.head(10).replace({np.nan: None}).to_dict(orient='records')

    return {
        "status": "ok", 
        "n_rows": n_rows,
        "columnas": columnas_finales,
        "preview": preview,
        "path": path_unificado
    }

def classify_target(series: pd.Series, n_rows: int) -> str:
    """
    Classify a target variable as 'classification' or 'regression' based on its unique values and ratio.
    
    Args:
        series: Pandas Series representing the target variable.
        n_rows: Total number of rows in the dataset."""
    nunique = series.nunique()
    ratio = nunique / n_rows

    if nunique == 2 or ratio < 0.05:
        return "classification"
    return "regression"

def classify_feature(series: pd.Series, n_rows: int) -> Dict[str, Any]:
    nunique = series.nunique()
    ratio = nunique / n_rows

    result = {
        "nunique": nunique,
        "r_ratio": round(ratio, 4),
    }

    if nunique == 2:
        result.update({"technical_level": 1, "subclass": "binary"})
    elif is_numeric_dtype(series) and nunique > 10:
        subclass = "continuous" if is_float_dtype(series) else "discrete"
        result.update({"technical_level": 3, "subclass": subclass})
    elif ratio < 0.05:
        result.update({"technical_level": 2, "subclass": "categorical"})
    elif ratio < 0.8:
        subclass = "continuous" if is_float_dtype(series) else "discrete"
        result.update({"technical_level": 3, "subclass": subclass})
    else:
        result.update({"technical_level": 4, "subclass": "high cardinality"})
    
    return result

def encode_series(series: pd.Series) -> pd.Series:
    if is_object_dtype(series) or is_string_dtype(series):
        return pd.Series(LabelEncoder().fit_transform(series.astype(str)), index=series.index)
    return series

def compute_information_gain(
    df: pd.DataFrame,
    feature: str,
    targets: list,
    target_meta: Dict[str, str],
    is_discrete: bool,
) -> Dict[str, float]:

    scores = {}

    for t in targets:
        temp_df = df[[feature, t]].dropna()

        if temp_df.empty:
            scores[t] = 0.0
            continue

        X = temp_df[[feature]].copy()
        y = temp_df[t].copy()

        try:
            X[feature] = encode_series(X[feature])
            y = encode_series(y)

            if target_meta[t] == "classification":
                score = mutual_info_classif(X, y, discrete_features=is_discrete)[0]
            else:
                score = mutual_info_regression(X, y, discrete_features=is_discrete)[0]

            scores[t] = round(float(score), 4)

        except Exception as e:
            logger.warning(f"IG error: {feature} vs {t} -> {e}")
            scores[t] = 0.0

    return scores

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
        
        df = pd.read_excel(data.path)
        df = df.fillna("")
        if df.empty:
            raise ValueError("Dataset is empty")
        
        if not data.targets:
            raise ValueError("No targets provided")
        
        n_rows = data.n_rows

        target_meta = {
            target: classify_target(df[target], n_rows)
            for target in data.targets
            if target in df.columns
        }
        columnas = list(data.targets)
        analysis_results = {}

        for col in data.features:
            if col not in df.columns:
                logger.warning(f"Column not found: {col}")
                continue

            nombre = col + "_limpio"
            if nombre in df.columns:

                col = nombre

            series = df[col]

            col_data = classify_feature(series, n_rows)

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
                is_discrete
            )
            analysis_results[col] = col_data

        sample_df = stratified_sample_100(df[columnas], data.targets)
        sample_df_clean = sample_df.astype(object).fillna("")
        metadata ={
            "n_rows": n_rows, 
            "targets": data.targets
        }

        print("Modelo: " + data.model)
        system_prompt = """/nothink
            You are a Data Science Assistant specialized in semantic feature classification.
            Your ONLY task: classify each feature in CATEGORICAL_SUBCLASS_EVALUATION as NOMINAL or ORDINAL.

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

            CLASSIFICATION RULES:
            1. ORDINAL: values have a natural, unambiguous order or hierarchy (e.g. Junior < Senior, Baja < Alta).
            2. NOMINAL: values are distinct categories with no inherent order (e.g. departments, service codes).
            3. Use representative_sample to observe how values relate to targets before deciding.
            4. If uncertain between ORDINAL and NOMINAL, default to NOMINAL.
            5. For ORDINAL, mapping must include ALL values from unique_pool, starting at 0.
            6. For NOMINAL, mapping must be null.

            STRICT OUTPUT RULES:
            - Output ONLY the # SEMANTIC_CLASSIFICATION_RESULTS block.
            - No explanations outside the reasoning field.
            - No recommendations, no observations, no markdown headers beyond the block.
            - No bullet points, no numbered lists.
            - One entry per feature, in the same order as CATEGORICAL_SUBCLASS_EVALUATION.
            """

        toon = build_toon_payload(metadata, analysis_results, sample_df_clean)
        user_prompt = toon
        with open("toon.json", "w", encoding="utf-8") as f:
            f.write(user_prompt)
        semantic_analysis = call_ollama(data.model, system_prompt, user_prompt)
        return {
            "status": "ok",
            "metadata": metadata,
            "analysis": analysis_results,
            "semantic": semantic_analysis, 
            "sample_df": sample_df_clean
        }

    except Exception as e:
        logger.error(f"process_state_1 failed: {e}")
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