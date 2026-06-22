"""
Módulo de la estrategia de orquestación paralela e independiente.

Estructura el plan para escenarios donde los objetivos no presentan correlaciones o ganancias de 
información mutua significativas, permitiendo paralelizar el entrenamiento de los estimadores.
"""

from .base import OrchestrationStrategy

class MultiOutputStrategy(OrchestrationStrategy):
    """
    Estrategia de ejecución paralela o independiente para objetivos desacoplados.
    
    Se utiliza cuando la ganancia de información o correlación cruzada mutua entre variables 
    objetivo cae por debajo del umbral mínimo configurado, entrenando un estimador aislado para 
    cada variable sin realizar propagación de predicciones intermedias.
    """
    @property
    def name(self) -> str:
        return 'MultiOutput'