import json
import os
from pydantic import BaseModel
from fastapi import APIRouter, File, UploadFile, Form
from typing import List
from app.services.processor import procesar_archivo
from services.backend.app.train_models import entrenar_modelos 
#from app.modelado_msql import entrenar_modelos

# 1. Usamos el APIRouter()
router = APIRouter()

@router.post("/upload") # 2. Cambiamos 'app.post' por 'router.post'
async def handle_upload(
    files: List[UploadFile] = File(...), 
    indices_to_preprocess: str = Form(...) # Recibimos como str para evitar errores 422
):
    try:
        to_process_list = json.loads(indices_to_preprocess) # Convertimos el string JSON a lista de índices
    except:
        to_process_list = [] # Si no es un JSON válido, asumimos que no se preprocesará nada
        
    res = []
    print(f"Recibidos {len(files)} archivos. Preprocesar: {to_process_list}")
    
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
    active: bool
    models: List[str]
    files: List[str]

class PredictionRequest(BaseModel):
    mio: PredictionBlock
    hombro: PredictionBlock
    prioridad: PredictionBlock


@router.post("/predict")
async def run_prediction(data: PredictionRequest):
    resultados_globales = {}

    # 1. Bloque Mío: Solo se procesa si el usuario lo activó
    if data.mio.active:
        res_mio = await procesar_bloque("MIO", data.mio, "etiqueta_mio")
        resultados_globales["mio"] = res_mio

    # 2. Bloque Hombro: Solo se procesa si el usuario lo activó
    if data.hombro.active:
        res_hombro = await procesar_bloque("HOMBRO", data.hombro, "etiqueta_hombro")
        resultados_globales["hombro"] = res_hombro

    # 3. Bloque Prioridad: Solo se procesa si el usuario lo activó
    if data.prioridad.active:
        res_prioridad = await procesar_bloque("PRIORIDAD", data.prioridad, "etiqueta_prioridad")
        resultados_globales["prioridad"] = res_prioridad

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


async def procesar_bloque(nombre_bloque: str, config: PredictionBlock, target_col: str, group_name: str):
    """
    Lógica genérica para verificar entrenamiento y realizar predicción por bloque.
    """
    if not config.active:
        return None

    resultados_bloque = {}
    modelos_en_disco = os.listdir('./models') # Lista de modelos ya entrenados en disco

    for model_key in config.models:
        nombre_modelo = f"{model_key}_{target_col}.pkl"
        
        # 1. ¿Hay que entrenar?
        if nombre_modelo not in modelos_en_disco:
            print(f"[{nombre_bloque}] Entrenando {model_key}...")
            await entrenar_modelos(config.files, [model_key], target_col)
        
        # 2. Predecir
        print(f"[{nombre_bloque}] Prediciendo con {model_key}...")
        res = await predecir_con_modelo(model_key, config.files, target_col)
        resultados_bloque[model_key] = res
        
    return resultados_bloque