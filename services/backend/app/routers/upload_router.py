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
    Handle file upload and basic inspection.
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
    except Exception as e:
        logger.error(f"Error en upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
