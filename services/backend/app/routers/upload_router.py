"""
Módulo de subida de archivos.

Gestiona la ruta encargada de recibir, validar y guardar archivos
de datasets iniciales subidos por el usuario.
"""
import logging
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas import UploadResponse
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload"])

@router.post("/upload", response_model=UploadResponse)
async def handle_upload(file: UploadFile = File(...)):
    """
    Ruta para procesar la subida de un dataset.
    
    Lee el archivo, extrae columnas y una previsualización de las filas,
    y guarda el archivo en el sistema de almacenamiento.
    """
    try:
        data = StorageService.read_dataset(file)

        n_rows = len(data)
        final_columns = data.columns.tolist()

        save_path = StorageService.save_dataset(data, f"uploads/{file.filename}")

        # Limpiar valores problemáticos para JSON
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        # Convertir NaN a None (compatible con JSON)
        preview = data.head(10).replace({np.nan: None}).to_dict(orient='records')

        return UploadResponse(
            status="ok",
            n_rows=n_rows,
            columnas=final_columns,
            preview=preview,
            path=save_path
        )
    except Exception as exc:
        logger.error("Error en upload: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
