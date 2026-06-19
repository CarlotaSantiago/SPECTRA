from typing import List, Dict, Any
from .base import OrchestrationStrategy

class GatedChainStrategy(OrchestrationStrategy):
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
