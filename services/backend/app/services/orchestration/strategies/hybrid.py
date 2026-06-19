from .base import OrchestrationStrategy

class HybridChainStrategy(OrchestrationStrategy):
    @property
    def name(self) -> str:
        return 'HybridChain'
