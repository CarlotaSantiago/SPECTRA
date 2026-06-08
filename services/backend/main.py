from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # IMPORTANTE
from app.routes import router
import os


app = FastAPI()

os.makedirs('uploads', exist_ok=True)
os.makedirs('model', exist_ok=True)
# 3. CONFIGURACIÓN DE CORS (Sin esto, el navegador bloqueará la petición)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # URL de tu Vite
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router) # Asegúrate de incluir tus rutas aquí si las tienes en otro archivo