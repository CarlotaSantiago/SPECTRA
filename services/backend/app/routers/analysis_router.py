import os
import json
import logging
import numpy as np
from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from app.schemas import ManifestSchema, PageResponse
from app.services.storage_service import StorageService
from app.services.analysis_facade import AnalysisFacade

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])

@router.get("/get-page", response_model=PageResponse)
def get_page(path: str, page: int = 1, size: int = 150, filters: str = "{}"):
    try:
        data = StorageService.read_dataset(path)

        try:
            filter_dict = json.loads(filters)
            for col, value in filter_dict.items():
                if value and col in data.columns:
                    data = data[data[col].astype(str).str.contains(str(value), case=False, na=False)]
        except Exception as f_err:
            logger.warning(f"Error parseando filtros: {f_err}")

        n_rows = len(data)
        start = (page - 1) * size
        end = start + size

        data_page = data.iloc[start:end].replace({np.nan: None, np.inf: None, -np.inf: None})

        return PageResponse(
            status="ok",
            items=data_page.to_dict(orient='records'),
            n_rows=n_rows,
            page=page,
            size=size
        )
    except Exception as e:
        logger.error(f"Error en get_page: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process-state1")
async def process_state_1(data: ManifestSchema) -> Dict[str, Any]:
    try:
        return await AnalysisFacade.process_dataset(data)
    except Exception as e:
        logger.error(f"process_state_1 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
