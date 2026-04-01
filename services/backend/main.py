from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware # IMPORTANTE
from typing import List

app = FastAPI()

# 3. CONFIGURACIÓN DE CORS (Sin esto, el navegador bloqueará la petición)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # URL de tu Vite
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
async def test():
    print("¡Petición recibida en el backend!")
    return {"message": "¡Servidor en funcionamiento!"}

@app.post("/upload")
async def handle_upload(
    files: List[UploadFile] = File(...), 
    preprocess: str = Form(...)
):
    is_preprocess = preprocess.lower() == "true"
    
    print(f"Archivos recibidos: {len(files)}")
    print(f"¿Preprocesar?: {is_preprocess}")
    
    return {"status": "ok", "received": len(files)}