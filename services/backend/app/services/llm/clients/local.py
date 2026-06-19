from .base import BaseOllamaClient

class LocalOllamaClient(BaseOllamaClient):
    """
    Cliente concreto para servidor Ollama local.
    """
    def __init__(self):
        super().__init__("http://localhost:11434")
