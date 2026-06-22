"""
Modulo de rutas para modelos y ejecucion.

Controla la obtencion de los modelos LLM disponibles, asi como
la segunda y tercera fase de la arquitectura (process_state_2, send-script).
"""
import os
import json
import logging
from typing import Dict, Any
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import ModelsResponse
from app.services.training_service_proxy import (
    proxy_llm_providers,
    proxy_process_state2,
    proxy_execute_script
)
from app.services.llm.script_patcher import (
    extract_user_training_params,
    inject_light_params,
    patch_training_params,
    LIGHT_CV_FOLDS,
    LIGHT_MAX_TRIALS,
)

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
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Ollama local no disponible: %s", exc)
        local_models = ["llama3", "qwen2.5-coder:7b"]

    # 2. Consumimos el endpoint externo
    try:
        url_profesor = "http://ia.drordas.info:11434/v1/models"
        response_profe = requests.get(url_profesor, timeout=3)

        if response_profe.status_code == 200:
            data_profe = response_profe.json()
            for model in data_profe.get("data", []):
                model_id = model.get("id")
                if model_id:
                    profesor_models.append(f"ia.drordas.info/{model_id}")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("[BACKEND] No se pudo conectar a la URL externa: %s", exc)

    return ModelsResponse(status="ok", models=local_models + profesor_models)


@router.get("/llm/providers")
def get_llm_providers():
    """Obtiene los proveedores de LLMs permitidos desde el proxy del servicio proxy."""
    try:
        body, status = proxy_llm_providers()
        return JSONResponse(content=body, status_code=status)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/process-state2")
def process_state_2(data: Dict[str, Any]):
    """
    Ejecuta el Stage 2 llamando al servicio proxy.

    Estrategia de generacion rapida + parcheo posterior:
      1. Extrae los parametros reales del usuario (cv_folds, max_trials).
      2. Inyecta valores minimos (cv_folds=2, max_trials=2) en el payload
         antes de enviarlo al training service para que el LLM genere el
         script sin un entrenamiento largo.
      3. Tras recibir el script generado, lo parchea con los valores reales
         usando script_patcher (solo cv_folds y max_trials; timeout intacto).
    """
    try:
        # 1. Guardar los valores reales que configuro el usuario
        real_params = extract_user_training_params(data)
        logger.info(
            "Parametros reales del usuario: cv_folds=%s, max_trials=%s",
            real_params["cv_folds"], real_params["max_trials"]
        )

        # 2. Inyectar valores light antes de llamar al proxy
        light_payload = inject_light_params(data)
        logger.info(
            "Enviando al training service con valores light: cv_folds=%d, max_trials=%d",
            LIGHT_CV_FOLDS, LIGHT_MAX_TRIALS
        )

        body, status_code = proxy_process_state2(light_payload)

        # 3. Parchar el script generado con los valores reales del usuario
        # El training service puede devolver el script en distintas claves
        script_key = None
        if "script" in body:
            script_key = "script"
        elif "generated_script" in body:
            script_key = "generated_script"

        # Solo parcheamos cv_folds y max_trials; el timeout lo deja el LLM tal cual
        has_real_params = (
            real_params["cv_folds"] is not None
            or real_params["max_trials"] is not None
        )

        if script_key and has_real_params:
            script_raw = body[script_key]
            patched_script, applied = patch_training_params(
                script=script_raw,
                max_trials=real_params["max_trials"],
                cv_folds=real_params["cv_folds"],
                timeout_minutes=None,  # timeout no se modifica
            )
            body[script_key] = patched_script
            body["patch_applied"] = applied
            logger.info("Script parcheado con valores reales. Variables sustituidas: %s", applied)
        else:
            logger.info(
                "No se encontro script en la respuesta o sin parametros de usuario para parchar. "
                "script_key=%s, has_real_params=%s",
                script_key, has_real_params
            )

        # 4. Propagamos el dossier original (con valores reales) al frontend para el state 3
        dossier_data = data.get("dossier", {})
        body["dossier"] = {
            "data": dossier_data
        }

        return JSONResponse(content=body, status_code=status_code)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("process_state_2 proxy failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/send-script")
def model_train(data: Dict[str, Any]):
    """
    Recibe el script Python validado (state 3) y lo envia al
    servicio proxy de ejecucion de entrenamiento, luego recolecta
    las metricas resultantes y las retorna al cliente.
    """
    try:
        script = data.get("script") or "# No script provided"

        # 1. Rutas locales para guardar el script temporal
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "model"))
        local_path = os.path.join(model_dir, "orchestation_script.py")
        linux_path = "uploads/datos_limpios.xlsx"

        # Crear directorio model/ si no existe
        os.makedirs(model_dir, exist_ok=True)
        logger.info("Model dir: %s", model_dir)

        # 2. Guardar el archivo localmente
        with open(local_path, "w", encoding="utf-8") as f_out:
            f_out.write(script)
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
        logger.info("proxy_execute_script -> status=%s", proxy_status)

        # Si el servicio de entrenamiento devolvio error, lo propagamos
        if proxy_status not in (200, 201):
            return JSONResponse(
                content={
                    "status": "error",
                    "message": proxy_body.get("message", "Training service error"),
                    "detail": proxy_body
                },
                status_code=proxy_status
            )

        # 4. LEER EL ARCHIVO JSON GENERADO POR EL ENTRENAMIENTO
        metrics_file_path = os.path.join(model_dir, "metrics.json")
        logger.info("Buscando metrics.json en: %s (existe=%s)",
                    metrics_file_path, os.path.exists(metrics_file_path))

        structured_body = {"targets": {}}

        if os.path.exists(metrics_file_path):
            with open(metrics_file_path, "r", encoding="utf-8") as f_in:
                structured_body = json.load(f_in)
            logger.info("Metricas cargadas con exito")
        else:
            logger.warning("No se encontro metrics.json en %s", metrics_file_path)
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Entrenamiento finalizado sin metrics.json"
                },
                status_code=500
            )

        # 5. Enviamos al frontend el JSON estructurado
        return JSONResponse(content=structured_body, status_code=200)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Error en /send-script: %s", exc)
        return JSONResponse(content={"status": "error", "message": str(exc)}, status_code=500)