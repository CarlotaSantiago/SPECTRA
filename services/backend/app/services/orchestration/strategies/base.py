"""
Módulo de la clase base para las estrategias de orquestación multi-output.

Define la interfaz abstracta común que expone las propiedades estructurales básicas 
y los métodos de serialización requeridos por todas las estrategias concretas del pipeline.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class OrchestrationStrategy(ABC):
    """
    Clase base abstracta para definir la estructura de las estrategias de orquestación.
    
    Proporciona un constructor unificado para almacenar el orden topológico de las variables, 
    las dependencias condicionales de exclusión (gating) y los coeficientes de correlación máximos, 
    además de un método para serializar la estrategia a diccionarios estándar nativos.
    """
    def __init__(self, order: Optional[List[str]] = None, gating: Optional[str] = None, dependents: Optional[List[str]] = None, max_dependency: float = 0.0):
        self.order = order or []
        self.gating = gating
        self.dependents = dependents or []
        self.max_dependency = max_dependency

    @property
    @abstractmethod
    def name(self) -> str:
        """Retorna el nombre identificador único de la estrategia de orquestación."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia de la estrategia y sus propiedades en un diccionario serializable."""
        return {
            'strategy': self.name,
            'order': self.order,
            'gating': self.gating,
            'dependents': self.dependents,
            'max_dependency': self.max_dependency
        }