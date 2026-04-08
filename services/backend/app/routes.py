import json

from fastapi import APIRouter, File, UploadFile, Form
from typing import List
# IMPORTANTE: Importamos 'procesar_archivo', que es el nombre en processor.py
from app.services.processor import procesar_archivo 

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