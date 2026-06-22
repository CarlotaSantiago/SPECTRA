"""
Módulo base e interfaz abstracta para clientes de Modelos de Lenguaje (LLM).

Define el contrato estructural (Strategy Pattern) para todas las conexiones e interacciones 
con las APIs de inferencia y proporciona una implementación genérica HTTP asíncrona para 
el consumo del endpoint de chat estructurado de Ollama.
"""

from abc import ABC, abstractmethod
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ILLMClient(ABC):
    """
    Strategy/Interface para los clientes de LLM.
    Define el contrato para la generación de texto.
    """
    @abstractmethod
    async def generate(self, model_name: str, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Contrato asíncrono obligatorio para la ejecución y retorno de inferencias del LLM."""
        pass

class BaseOllamaClient(ILLMClient):
    """
    Implementación base común para los clientes de Ollama.
    
    Gestiona el ciclo de vida de las solicitudes de red mediante peticiones POST no bloqueantes, 
    el empaquetado seguro de los roles del sistema y usuario, y el control de hiperparámetros 
    críticos como la temperatura, muestreo probabilístico (*top_p*) y longitud de respuesta.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def generate(self, model_name: str, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": options or {
                "temperature": 0.1,
                "top_p": 0.8,
                "num_predict": 4096 # Reemplaza max_tokens para Ollama
            }
        }
        
        try:
            logger.info(f"Consultando modelo '{model_name}' en '{self.base_url}'...")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                
                logger.info("Respuesta del LLM recibida correctamente.")
                content = response.json()
                
                msg_content = content.get('message', {}).get('content')
                if not msg_content:
                    msg_content = content.get('response', '')
                    
                return msg_content
                
        except Exception as e:
            logger.error(f"Error comunicándose con Ollama ({self.base_url}): {e}")
            return '{"error": "No se pudo obtener respuesta de la IA"}'