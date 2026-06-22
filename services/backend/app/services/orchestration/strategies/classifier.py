"""
Módulo de la estrategia de encadenamiento para tareas de clasificación.

Implementa la orquestación secuencial de variables categóricas nominales u ordinales, 
propagando las predicciones intermedias de los primeros clasificadores hacia los siguientes.
"""

from typing import List, Dict, Any
from .base import OrchestrationStrategy

class ClassifierChainStrategy(OrchestrationStrategy):
    """
    Estrategia orientada al encadenamiento secuencial de modelos de clasificación multietiqueta.
    
    Extiende la estructura base inyectándole perfiles detallados por cada objetivo categórico 
    (subclase nominal/ordinal, mapeos internos y cardinalidad de clases), permitiendo al pipeline 
    conocer los requisitos exactos de codificación antes de alimentar predicciones pasadas como features.
    """
    def __init__(self, order: List[str], target_profiles: Dict[str, Any], max_dependency: float = 0.0):
        super().__init__(order=order, max_dependency=max_dependency)
        self.target_profiles = target_profiles

    @property
    def name(self) -> str:
        return 'ClassifierChain'
        
    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base['target_profiles'] = self.target_profiles
        return base