"""
Módulo de factoría y adaptadores para la gestión de clientes LLM.

Implementa un patrón Factory para conmutar dinámicamente entre instancias de clientes 
locales y remotos basándose en el nombre o patrón de la dirección del modelo solicitado. 
Además, expone una función adaptadora para garantizar compatibilidad hacia atrás.
"""

from .clients.base import ILLMClient
from .clients.local import LocalOllamaClient
from .clients.remote import RemoteOllamaClient

class LLMClientFactory:
    """
    Patrón Factory para crear el cliente LLM adecuado.
    
    Evalúa la nomenclatura del identificador del modelo; si detecta firmas de dominio 
    o subdominios remotos, despacha un cliente remoto. De lo contrario, inicializa el 
    entorno por defecto para ejecuciones de servidor en la máquina local.
    """
    @staticmethod
    def create_client(model_name: str) -> ILLMClient:
        if "ia.drordas.info" in model_name or "." in model_name:
            return RemoteOllamaClient()
        return LocalOllamaClient()

# Adapter temporal para mantener compatibilidad hacia atrás
async def call_ollama(model_name: str, system_prompt: str, user_prompt: str, state: int = 0, attempt: int = 1) -> str:
    """
    Función adaptadora asíncrona para conservar la compatibilidad con llamadas tradicionales.
    
    Resuelve la inicialización del cliente de forma transparente a través de la factoría 
    y despacha la petición de inferencia abstrayendo la lógica de la API de mensajería del LLM.
    """
    client = LLMClientFactory.create_client(model_name)
    return await client.generate(model_name, system_prompt, user_prompt)