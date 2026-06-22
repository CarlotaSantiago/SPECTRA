"""
Módulo de rutas de análisis.

Contiene los endpoints encargados de la paginación de datos (get_page) y
el procesamiento inicial del dataset (process_state1) a través del facade.
"""
import os
import json
import logging
from typing import Any, Dict
import numpy as np
from fastapi import APIRouter, HTTPException

from app.schemas import ManifestSchema, PageResponse
from app.services.storage_service import StorageService
from app.services.analysis_facade import AnalysisFacade

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])

@router.get("/get-page", response_model=PageResponse)
def get_page(path: str, page: int = 1, size: int = 150, filters: str = "{}"):
    """
    Obtiene una página paginada del dataset, aplicando filtros si los hay.
    
    Parámetros:
        path (str): Ruta al dataset.
        page (int): Número de página (empieza en 1).
        size (int): Tamaño de la página.
        filters (str): String JSON con filtros por columna.
    """
    try:
        data = StorageService.read_dataset(path)

        try:
            filter_dict = json.loads(filters)
            for col, value in filter_dict.items():
                if value and col in data.columns:
                    # Filtra las filas que contienen el string introducido
                    data = data[data[col].astype(str).str.contains(
                        str(value), case=False, na=False
                    )]
        except Exception as f_err:
            logger.warning("Error parseando filtros: %s", f_err)

        n_rows = len(data)
        start = (page - 1) * size
        end = start + size

        # Se reemplazan los valores no soportados por JSON
        data_page = data.iloc[start:end].replace({np.nan: None, np.inf: None, -np.inf: None})

        return PageResponse(
            status="ok",
            items=data_page.to_dict(orient='records'),
            n_rows=n_rows,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.error("Error en get_page: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/process-state1")
async def process_state_1(data: ManifestSchema) -> Dict[str, Any]:
    """
    Inicia la primera etapa del análisis (State 1).
    Utiliza el AnalysisFacade para orquestar la clasificación de datos.
    """
    try:
        return await AnalysisFacade.process_dataset(data)
    except Exception as exc:
        logger.error("process_state_1 failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
