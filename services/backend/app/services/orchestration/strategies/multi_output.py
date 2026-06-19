from .base import OrchestrationStrategy

class MultiOutputStrategy(OrchestrationStrategy):
    @property
    def name(self) -> str:
        return 'MultiOutput'
