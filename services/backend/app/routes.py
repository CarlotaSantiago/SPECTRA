from http.client import HTTPException
import io
import os
import json
import numpy as np
import pandas as pd
from typing import List
from pydantic import BaseModel
from app.services.processor import limpiar_datos
from fastapi import APIRouter, File, UploadFile, Form
from app.services.predict_models import predecir_final
from app.services.train_models import entrenar_modelos_binarios, entrenar_modelos_prioridad


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

    n_total = len(df_unificado) # Número total de filas en el DataFrame unificado
    columnas_finales = df_unificado.columns.tolist() # Lista de columnas finales

    path_unificado = os.path.join("uploads", "dataset_unificado.xlsx")
    df_unificado.to_excel(path_unificado, index=False)

    # Limpiar valores problemáticos para JSON
    df_unificado.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Convertir NaN a None (compatible con JSON)
    preview = df_unificado.head(10).replace({np.nan: None}).to_dict(orient='records')

    return {
        "status": "ok", 
        "n_total": n_total,
        "columnas": columnas_finales,
        "preview": preview,
        "path": path_unificado
    }


@router.post("/api/process-state-1") # 2. Cambiamos 'app.post' por 'router.post'
def process_state_1(
    n_rows: int = Form(...),
    path: str = Form(...),
    features: str = Form(...),
    targets: str = Form(...),
    mandatory: str = Form(...)
):
    """
    Process file for Etapa 1 by applying cleaning functions to specified columns.
    
    Args:
        file: Uploaded file to process.
        indices_to_preprocess: JSON string containing indices of files to preprocess.
    Returns:
        Status and results of the processing.
    """
    try:
        features_list = json.loads(features)
        targets_list = json.loads(targets)
        mandatory_list = json.loads(mandatory)

        df = pd.read_csv(path)

        analysis_results = {}

        for col in features_list:
            nunique = df[col].nunique()
            r_ratio = nunique / n_rows

            col_data = {
                "nunique": nunique,
                "r_ratio": round(r_ratio, 4),
                "user_mandatory": col in mandatory_list,
                "unique_pool": df[col].unique().tolist()[:20] # Limitamos para no saturar si hay muchas
            }

            # Lógica de Clasificación por Niveles
            if nunique == 2:
                col_data["technical_level"] = 1
                col_data["subclass"] = "Binary"
            
            elif r_ratio < 0.05:
                col_data["technical_level"] = 2
                # Aquí marcamos que requiere intervención del LLM
                col_data["subclass"] = "PENDING_LLM" 
            
            elif 0.05 <= r_ratio < 0.80:
                col_data["technical_level"] = 3
                # Clasificación según el tipo de dato de pandas
                if pd.api.types.is_float_dtype(df[col]):
                    col_data["subclass"] = "Continua"
                else:
                    col_data["subclass"] = "Discreta"
            
            else:
                col_data["technical_level"] = 4
                col_data["subclass"] = "Alta Cardinalidad"
            
            analysis_results[col] = col_data

        return {
            "status": "ok",
            "analysis": analysis_results,
            "targets": targets_list
        }
    except Exception as e:
        print(f"Error en process_etapa_1: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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