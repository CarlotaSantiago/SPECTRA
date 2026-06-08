import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

TRAINING_SERVICE_URL = os.getenv("TRAINING_SERVICE_URL", "http://localhost:8001").rstrip("/")
TRAINING_SERVICE_TIMEOUT = float(os.getenv("TRAINING_SERVICE_TIMEOUT", "1200"))


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
