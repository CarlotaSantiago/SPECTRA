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
        body["user_constraints"] = data["user_constraints"]
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
        local_path = os.path.abspath(os.path.join(current_dir, "..", "model", "orchestation_script.py"))
        linux_path = "uploads/datos_limpios.xlsx"

        
        # 2. Guardar el archivo localmente
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(script)

        # payload estructurado para lanzar el proceso en el otro micro/contenedor
        payload_to_proxy = {
            "script": script,
            "path": linux_path,
            "output_path": "./model",
            "manifest": {
                "additionalProp1": {}
            }
        }  
        
        # 3. Se ejecuta el entrenamiento (esto genera los logs en consola y el archivo en disco)
        response_status = proxy_execute_script(payload_to_proxy)
        
        # 4. LEER EL ARCHIVO JSON GENERADO POR EL ENTRENAMIENTO
        # Apuntamos a la ruta donde tu script de Python guardó el JSON estructurado
        metrics_file_path = os.path.abspath(os.path.join(current_dir, "..", "model", "metrics.json"))
        
        # Inicializamos un body vacío por si algo falla
        structured_body = {"targets": {}}
        
        if os.path.exists(metrics_file_path):
            with open(metrics_file_path, "r", encoding="utf-8") as f:
                structured_body = py_json.load(f)
            print("¡Archivo de métricas estructurado cargado con éxito!")
        else:
            print(f"Advertencia: No se encontró el archivo de métricas en {metrics_file_path}")
            # Si no existe, puedes devolver un error o construir una respuesta alternativa 
            return JSONResponse(
                content={"status": "error", "message": "El entrenamiento terminó pero no generó el reporte metrics.json"}, 
                status_code=500
            )

        # 5. Enviamos al frontend el JSON estructurado con la clave 'targets' directamente
        return JSONResponse(content=structured_body, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)