"""
Módulo de análisis estructural y ordenamiento de dependencias para variables objetivo.

Permite identificar patrones de ausencia de datos no aleatorios (MNAR) mediante variables de 
activación o compuerta (*gating*). Asimismo, resuelve el orden topológico óptimo en que deben 
entrenarse y encadenarse los modelos de predicción basándose en su puntuación de influencia mutua.
"""

import pandas as pd

def detect_structural_absences(df: pd.DataFrame, targets: list[str], umbral: float = 0.95) -> dict | None:     
    """
    Detecta ausencias estructurales (MNAR) que condicionan la existencia de otras variables.
    
    Analiza si la ausencia o invalidez semántica de una variable objetivo condicional ($t_1$) 
    implica de forma sistemática (bajo un umbral de confianza probabilístico) la ausencia de un 
    subconjunto de variables dependientes ($t_2$), aislando comportamientos condicionales en el dataset.
    """
    print("Detecting structural absences with umbral:", umbral)
    for t1 in targets: 
        mask = df[t1].isna() | (df[t1].astype(str).str.strip().isin(['OTHER', 'otros', 'NaN', 'nan', '']))
        if mask.sum() == 0:             
            continue           
        dependents = [ 
            t2 for t2 in targets             
            if t2 != t1 and (df.loc[mask, t2].isna() | df.loc[mask, t2].astype(str).str.strip().isin(['NaN', 'nan', ''])).mean() >= umbral         
        ] 
        if dependents:  
            print(f"Structural absence detected: {t1} with dependents {dependents}")           
            return {'gating': t1, 'dependents': dependents}     
    return None

def resolve_chain_order(dependency_matrix, threshold):
    """
    Resuelve heurísticamente el orden de ejecución y alimentación en cadenas de predictores.
    
    Calcula una puntuación de influencia para cada variable objetivo sumando sus coeficientes 
    de correlación significativos (que superan el umbral establecido). Ordena las variables de 
    mayor a menor impacto para asegurar que los modelos con mayor capacidad predictiva sobre otros 
    se sitúen al inicio de la cadena.
    """
    influence_scores = {}
    targets = dependency_matrix.columns.tolist()

    for t in targets:
        row_scores = dependency_matrix.loc[t]
        filtered_scores = [
            score for label, score in row_scores.items()
            if label != t and score >= threshold
        ]
        influence_scores[t] = sum(filtered_scores)

    return sorted(influence_scores, key=influence_scores.get, reverse=True)