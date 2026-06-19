import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

TRAINING_SERVICE_URL = os.getenv("TRAINING_SERVICE_URL", "http://localhost:8001").rstrip("/")
TRAINING_SERVICE_TIMEOUT = float(os.getenv("TRAINING_SERVICE_TIMEOUT", "1200"))
LLM_PROVIDERS_TIMEOUT = 5.0

_EMPTY_LLM_PROVIDERS: dict[str, Any] = {
    "default_provider": "ollama",
    "default_model": "",
    "providers": [],
}

def proxy_execute_script(data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    url = f"{TRAINING_SERVICE_URL}/process-state2/execute-script"

    try:
        response = requests.post(
            url,
            json=data,
            timeout=TRAINING_SERVICE_TIMEOUT,
        )
    except requests.exceptions.ConnectionError as exc:
        logger.error("Training service unavailable at %s: %s", url, exc)
        return {
            "status": "error",
            "message": f"Training service unavailable at {TRAINING_SERVICE_URL}",
        }, 503
    except requests.exceptions.Timeout:
        logger.error("Training service timed out after %ss", TRAINING_SERVICE_TIMEOUT)
        return {
            "status": "error",
            "message": f"Training service timed out after {TRAINING_SERVICE_TIMEOUT}s",
        }, 504
    except requests.exceptions.RequestException as exc:
        logger.error("Training service request failed: %s", exc)
        return {
            "status": "error",
            "message": f"Training service request failed: {exc}",
        }, 500

    try:
        body = response.json()
    except ValueError:
        logger.error(
            "Training service returned non-JSON response (HTTP %s)",
            response.status_code,
        )
        return {
            "status": "error",
            "message": "Training service returned an invalid response",
        }, 502

    return body, response.status_code

def proxy_process_state2(data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    url = f"{TRAINING_SERVICE_URL}/process-state2"
    try:
        response = requests.post(
            url,
            json=data,
            timeout=TRAINING_SERVICE_TIMEOUT,
        )
    except requests.exceptions.ConnectionError as exc:
        logger.error("Training service unavailable at %s: %s", url, exc)
        return {
            "status": "error",
            "message": f"Training service unavailable at {TRAINING_SERVICE_URL}",
        }, 200
    except requests.exceptions.Timeout:
        logger.error("Training service timed out after %ss", TRAINING_SERVICE_TIMEOUT)
        return {
            "status": "error",
            "message": f"Training service timed out after {TRAINING_SERVICE_TIMEOUT}s",
        }, 200
    except requests.exceptions.RequestException as exc:
        logger.error("Training service request failed: %s", exc)
        return {
            "status": "error",
            "message": f"Training service request failed: {exc}",
        }, 200

    try:
        body = response.json()
    except ValueError:
        logger.error(
            "Training service returned non-JSON response (HTTP %s)",
            response.status_code,
        )
        return {
            "status": "error",
            "message": "Training service returned an invalid response",
        }, 200

    return body, response.status_code


def proxy_llm_providers() -> tuple[dict[str, Any], int]:
    url = f"{TRAINING_SERVICE_URL}/llm/providers"
    try:
        response = requests.get(url, timeout=LLM_PROVIDERS_TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        logger.warning("Training service unavailable for LLM providers at %s: %s", url, exc)
        return _EMPTY_LLM_PROVIDERS.copy(), 200
    except requests.exceptions.Timeout:
        logger.warning("Training service LLM providers timed out after %ss", LLM_PROVIDERS_TIMEOUT)
        return _EMPTY_LLM_PROVIDERS.copy(), 200
    except requests.exceptions.RequestException as exc:
        logger.warning("Training service LLM providers request failed: %s", exc)
        return _EMPTY_LLM_PROVIDERS.copy(), 200

    try:
        body = response.json()
    except ValueError:
        logger.warning(
            "Training service returned non-JSON LLM providers response (HTTP %s)",
            response.status_code,
        )
        return _EMPTY_LLM_PROVIDERS.copy(), 200

    return body, response.status_code
