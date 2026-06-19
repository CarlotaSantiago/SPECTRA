from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class OrchestrationStrategy(ABC):
    """
    Clase base para las estrategias de orquestación.
    """
    def __init__(self, order: Optional[List[str]] = None, gating: Optional[str] = None, dependents: Optional[List[str]] = None, max_dependency: float = 0.0):
        self.order = order or []
        self.gating = gating
        self.dependents = dependents or []
        self.max_dependency = max_dependency

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy': self.name,
            'order': self.order,
            'gating': self.gating,
            'dependents': self.dependents,
            'max_dependency': self.max_dependency
        }
