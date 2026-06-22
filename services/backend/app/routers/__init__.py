"""
Módulo de enrutamiento principal.

Centraliza e incluye todos los routers secundarios (análisis, modelos, subida de archivos)
para ser conectados a la aplicación FastAPI principal.
"""

from fastapi import APIRouter

from .analysis_router import router as analysis_router
from .model_router import router as model_router
from .upload_router import router as upload_router

# Creamos un router principal unificado
router = APIRouter()

# Incluimos cada submódulo
router.include_router(analysis_router)
router.include_router(model_router)
router.include_router(upload_router)