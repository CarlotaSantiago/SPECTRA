"""
Módulo del cliente concreto de inferencia distribuida o remota.

Establece canales de comunicación hacia endpoints externos de Ollama e introduce filtros 
de parseo semántico en los selectores de modelos para evitar colisiones de rutas remotas.
"""

from typing import Dict, Any, Optional
from .base import BaseOllamaClient

class RemoteOllamaClient(BaseOllamaClient):
    """
    Cliente concreto para servidor Ollama remoto.
    
    Apunta a un dominio centralizado e intercepta las solicitudes de generación de texto 
    para limpiar los nombres cualificados de los modelos (removiendo esquemas de URIs o subrutas), 
    garantizando que el nodo remoto reconozca el tag crudo del modelo disponible en su registro.
    """
    def __init__(self):
        super().__init__("http://ia.drordas.info:11434")
        
    async def generate(self, model_name: str, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        # Limpieza del nombre del modelo para uso remoto
        clean_model_name = model_name.split("/")[-1] if "/" in model_name else model_name
        return await super().generate(clean_model_name, system_prompt, user_prompt, options)