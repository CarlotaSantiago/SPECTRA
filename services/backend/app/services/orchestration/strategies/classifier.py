from typing import List, Dict, Any
from .base import OrchestrationStrategy

class ClassifierChainStrategy(OrchestrationStrategy):
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
