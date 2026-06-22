"""
Módulo del cliente concreto de inferencia local.

Especializa el comportamiento base apuntando los sockets de conexión HTTP hacia el demonio 
u orquestador de Ollama desplegado localmente en el puerto estándar del sistema.
"""

from .base import BaseOllamaClient

class LocalOllamaClient(BaseOllamaClient):
    """
    Cliente concreto para servidor Ollama local.
    
    Configura la dirección de loopback local (`localhost:11434`) para canalizar las consultas 
    y tokens directamente al hardware o servicio interno sin salir de la infraestructura de la máquina.
    """
    def __init__(self):
        super().__init__("http://localhost:11434")