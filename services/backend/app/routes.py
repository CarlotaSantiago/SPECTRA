import json
import os
import asyncio
from pydantic import BaseModel
from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from typing import List
from app.services.processor import procesar_archivo
from app.services.train_models import entrenar_modelos_binarios, entrenar_modelos_prioridad
from app.services.predict_models import predecir_final

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

    res = []
    
    for index, file in enumerate(files):
        debe_limpiar = index in to_process_list
        # 3. Llamamos a la función correcta con 'await'
        result = await procesar_archivo(file, debe_limpiar)
        res.append({
            "filename": file.filename,
            "preprocessed": debe_limpiar,
            "data": result
        })

    return {
        "status": "ok", 
        "received": len(files),
        "results": res
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