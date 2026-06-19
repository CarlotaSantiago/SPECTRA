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
        return JSONResponse(content=body, status_code=status_code)
    except Exception as e:
        logger.error("process_state_2 proxy failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-script")
def entreno(data: ScriptExecutionPayload):
    try:
        script = data.script or "# No script provided"

        # Inyectar parámetros de entrenamiento elegidos por el usuario
        if any(p is not None for p in [data.max_trials, data.cv_folds, data.timeout_minutes]):
            script, applied = patch_training_params(
                script=script,
                max_trials=data.max_trials,
                cv_folds=data.cv_folds,
                timeout_minutes=data.timeout_minutes,
            )
            logger.info(
                "Script parcheado con parámetros de usuario: %s",
                {k: v for k, v in {
                    'max_trials': data.max_trials,
                    'cv_folds': data.cv_folds,
                    'timeout_minutes': data.timeout_minutes,
                }.items() if v is not None}
            )
            if applied:
                logger.debug("Variables sustituidas en el script: %s", applied)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.abspath(os.path.join(current_dir, "..", "..", "model", "orchestation_script.py"))
        linux_path = "uploads/datos_limpios.xlsx"

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(script)

        payload_to_proxy = {
            "script": script,
            "path": linux_path,
            "output_path": "./model",
            "manifest": {"additionalProp1": {}}
        }

        response_body, response_status = proxy_execute_script(payload_to_proxy)

        metrics_file_path = os.path.abspath(os.path.join(current_dir, "..", "..", "model", "metrics.json"))
        structured_body = {"targets": {}}

        if os.path.exists(metrics_file_path):
            with open(metrics_file_path, "r", encoding="utf-8") as f:
                structured_body = json.load(f)
            logger.info("¡Archivo de métricas estructurado cargado con éxito!")
        else:
            logger.warning(f"No se encontró el archivo de métricas en {metrics_file_path}")
            raise HTTPException(status_code=500, detail="El entrenamiento terminó pero no generó el reporte metrics.json")

        return JSONResponse(content=structured_body, status_code=response_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en entreno: {e}")
        raise HTTPException(status_code=500, detail=str(e))
