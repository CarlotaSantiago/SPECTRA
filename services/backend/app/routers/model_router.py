import os
import json
import logging
import requests
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import ModelsResponse, ScriptExecutionPayload
from app.services.training_service_proxy import proxy_llm_providers, proxy_process_state2, proxy_execute_script
from app.services.llm.script_patcher import patch_training_params

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Models & Execution"])

@router.get("/models", response_model=ModelsResponse)
def get_available_models():
    """
    Lista los modelos locales y consume de forma exacta la API 
    del proveedor externo detectada en el test.
    """
    local_models = []
    profesor_models = []

    # 1. Intentamos recuperar los modelos locales (Ollama local API)
    try:
        response_local = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response_local.status_code == 200:
            local_models = [m["name"] for m in response_local.json().get("models", [])]
    except Exception as e:
        logger.warning(f"Ollama local no disponible: {e}")
        local_models = ["llama3", "qwen2.5-coder:7b"]

    # 2. Consumimos el endpoint externo
    try:
        url_profesor = "http://ia.drordas.info:11434/v1/models"
        response_profe = requests.get(url_profesor, timeout=3)

        if response_profe.status_code == 200:
            data_profe = response_profe.json()
            for m in data_profe.get("data", []):
                model_id = m.get("id")
                if model_id:
                    profesor_models.append(f"ia.drordas.info/{model_id}")
    except Exception as e:
        logger.error(f"[BACKEND] No se pudo conectar a la URL externa: {e}")

    return ModelsResponse(status="ok", models=local_models + profesor_models)

@router.get("/llm/providers")
def get_llm_providers():
    try:
        body, status = proxy_llm_providers()
        return JSONResponse(content=body, status_code=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-state2")
def process_state_2(data: Dict[str, Any]):
    try:
        body, status_code = proxy_process_state2(data)
        
        # Propagamos el dossier o los constraints de vuelta al frontend para el state 3
        dossier_data = data.get("dossier", {})
        body["dossier"] = {
            "data": dossier_data
        }
        
        return JSONResponse(content=body, status_code=status_code)
    except Exception as e:
        logger.error("process_state_2 proxy failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-script")
def entreno(data: Dict[str, Any]):
    try:
        script = data.get("script") or "# No script provided"
        
        # 1. Rutas locales para guardar el script temporal
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # current_dir = .../services/backend/app/routers/
        # Subimos 3 niveles: routers → app → backend, luego entramos a model/
        # Esto coincide con el volumen montado en docker-compose: ./services/backend/model → /app/model
        model_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "model"))
        local_path = os.path.join(model_dir, "orchestation_script.py")
        linux_path = "uploads/datos_limpios.xlsx"

        # Crear directorio model/ si no existe
        os.makedirs(model_dir, exist_ok=True)
        logger.info("Model dir: %s", model_dir)
        
        # 2. Guardar el archivo localmente
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(script)
        logger.info("Script guardado en: %s", local_path)

        # payload estructurado para lanzar el proceso en el otro micro/contenedor
        payload_to_proxy = {
            "script": script,
            "path": linux_path,
            "output_path": "./model",
            "manifest": {
                "additionalProp1": {}
            }
        }  
        
        # 3. Se ejecuta el entrenamiento
        proxy_body, proxy_status = proxy_execute_script(payload_to_proxy)
        logger.info("proxy_execute_script → status=%s body_keys=%s", proxy_status, list(proxy_body.keys()) if isinstance(proxy_body, dict) else proxy_body)

        # Si el servicio de entrenamiento devolvió error, lo propagamos
        if proxy_status not in (200, 201):
            return JSONResponse(
                content={"status": "error", "message": proxy_body.get("message", "Training service error"), "detail": proxy_body},
                status_code=proxy_status
            )
        
        # 4. LEER EL ARCHIVO JSON GENERADO POR EL ENTRENAMIENTO
        metrics_file_path = os.path.join(model_dir, "metrics.json")
        logger.info("Buscando metrics.json en: %s (existe=%s)", metrics_file_path, os.path.exists(metrics_file_path))
        
        # Inicializamos un body vacío por si algo falla
        structured_body = {"targets": {}}
        
        if os.path.exists(metrics_file_path):
            with open(metrics_file_path, "r", encoding="utf-8") as f:
                structured_body = json.load(f)
            logger.info("Métricas cargadas con éxito: %s targets", len(structured_body.get("targets", {})))
        else:
            logger.warning("No se encontró metrics.json en %s", metrics_file_path)
            return JSONResponse(
                content={"status": "error", "message": "El entrenamiento terminó pero no generó el reporte metrics.json"}, 
                status_code=500
            )

        # 5. Enviamos al frontend el JSON estructurado
        return JSONResponse(content=structured_body, status_code=200)
        
    except Exception as e:
        logger.exception("Error en /send-script: %s", e)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)