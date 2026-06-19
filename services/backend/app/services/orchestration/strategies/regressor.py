from .base import OrchestrationStrategy

class RegressorChainStrategy(OrchestrationStrategy):
    @property
    def name(self) -> str:
        return 'RegressorChain'
