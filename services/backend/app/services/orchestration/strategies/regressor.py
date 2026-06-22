"""
Módulo de la estrategia de encadenamiento para tareas de regresión continua.

Implementa la secuencia jerárquica para la propagación de variables numéricas, alimentando los 
modelos posteriores con los valores continuos inferidos por los predecesores en la cadena.
"""

from .base import OrchestrationStrategy

class RegressorChainStrategy(OrchestrationStrategy):
    """
    Estrategia orientada al encadenamiento secuencial de modelos de regresión numérica continua.
    
    Define una jerarquía de ordenación donde los estimadores numéricos se alimentan de forma mutua, 
    añadiendo de forma incremental las predicciones de los targets previos como nuevas características 
    de entrada para capturar tendencias multivariable.
    """
    @property
    def name(self) -> str:
        return 'RegressorChain'