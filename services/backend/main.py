# main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router # Ahora esto importará el __init__.py unificado

# Configuración básica de logs para que veas qué pasa en la consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TFG Pipeline API",
    description="Backend modular para entrenamiento y análisis de modelos en paralelo",
    version="1.0.0"
)

# Creamos directorios locales esenciales si no existen
os.makedirs('uploads', exist_ok=True)
os.makedirs('model', exist_ok=True)

# Configuración de CORS para conectar con el Frontend (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos el router centralizado con todas tus rutas limpias
app.include_router(router)
