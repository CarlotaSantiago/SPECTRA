"""
Módulo de la estrategia de orquestación por compuerta condicional.

Gestiona dependencias estructurales complejas donde la presencia o ausencia de 
ciertos datos condiciona de forma directa la existencia y ejecución de ramificaciones del modelo.
"""

from typing import List, Dict, Any
from .base import OrchestrationStrategy

class GatedChainStrategy(OrchestrationStrategy):
    """
    Estrategia jerárquica de compuerta condicional para abordar ausencias estructurales (MNAR).
    
    Encapsula una estructura de modelado`sub_strategy` (un flujo subordinado) que solo se 
    activa o evalúa si la variable condicional de activación (`gating`) se encuentra presente o cumple 
    ciertos criterios en los registros evaluados.
    """
    def __init__(self, gating: str, dependents: List[str], max_dependency: float, sub_strategy: OrchestrationStrategy):
        super().__init__(gating=gating, dependents=dependents, max_dependency=max_dependency)
        self.sub_strategy = sub_strategy

    @property
    def name(self) -> str:
        return 'GatedChain'

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base['sub_strategy'] = self.sub_strategy.to_dict()
        return base