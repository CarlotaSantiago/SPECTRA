from typing import Dict, Any, Optional
from .base import BaseOllamaClient

class RemoteOllamaClient(BaseOllamaClient):
    """
    Cliente concreto para servidor Ollama remoto.
    """
    def __init__(self):
        super().__init__("http://ia.drordas.info:11434")
        
    async def generate(self, model_name: str, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        # Limpieza del nombre del modelo para uso remoto
        clean_model_name = model_name.split("/")[-1] if "/" in model_name else model_name
        return await super().generate(clean_model_name, system_prompt, user_prompt, options)
