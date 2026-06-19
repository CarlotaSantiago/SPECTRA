# app/routes/__init__.py
from fastapi import APIRouter

# Importamos los routers individuales de tus archivos
# (Asegúrate de que los nombres de archivo coincidan con cómo llamaste a tus scripts)
from .analysis_router import router as analysis_router
from .model_router import router as model_router
from .upload_router import router as upload_router

# Creamos un router principal unificado
router = APIRouter()

# Incluimos cada submódulo con un prefijo limpio (opcional pero muy recomendado)
router.include_router(analysis_router)
router.include_router(model_router)
router.include_router(upload_router)