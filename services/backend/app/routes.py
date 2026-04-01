from fastapi import APIRouter, File, UploadFile, Form
from typing import List
# IMPORTANTE: Importamos 'procesar_archivo', que es el nombre en processor.py
from app.services.processor import procesar_archivo 

# 1. Usamos el APIRouter()
router = APIRouter()

@router.post("/upload") # 2. Cambiamos 'app.post' por 'router.post'
async def handle_upload(
    files: List[UploadFile] = File(...), 
    preprocess: str = Form(...) # Recibimos como str para evitar errores 422
):
    # Convertimos el string de JS ("true"/"false") a booleano de Python
    debe_limpiar = preprocess.lower() == "true"
    
    res = []
    print(f"Recibidos {len(files)} archivos. Preprocesar: {debe_limpiar}")
    
    for file in files:
        # 3. Llamamos a la función correcta con 'await'
        result = await procesar_archivo(file, debe_limpiar)
        res.append(result)
    
    return {
        "status": "ok", 
        "received": len(files),
        "results": res
    }