from .clients.base import ILLMClient
from .clients.local import LocalOllamaClient
from .clients.remote import RemoteOllamaClient

class LLMClientFactory:
    """
    Patrón Factory para crear el cliente LLM adecuado.
    """
    @staticmethod
    def create_client(model_name: str) -> ILLMClient:
        if "ia.drordas.info" in model_name or "." in model_name:
            return RemoteOllamaClient()
        return LocalOllamaClient()

# Adapter temporal para mantener compatibilidad hacia atrás
async def call_ollama(model_name: str, system_prompt: str, user_prompt: str, state: int = 0, attempt: int = 1) -> str:
    client = LLMClientFactory.create_client(model_name)
    return await client.generate(model_name, system_prompt, user_prompt)
