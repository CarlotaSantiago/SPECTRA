"""
Módulo de la estrategia de orquestación híbrida o mixta.

Permite coordinar de forma unificada problemas heterogéneos que combinan variables 
objetivo continuas (regresión) y categóricas (clasificación) dentro de una misma cadena.
"""

from .base import OrchestrationStrategy

class HybridChainStrategy(OrchestrationStrategy):
    """
    Estrategia adaptativa para escenarios con objetivos de naturaleza mixta (categóricos y numéricos).
    
    Orquesta el flujo de ejecución combinando encadenamientos de modelos de regresión y clasificación, 
    permitiendo la propagación de inferencias continuas y discretas de forma fluida a lo largo de la cadena.
    """
    @property
    def name(self) -> str:
        return 'HybridChain'