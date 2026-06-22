"""
Módulo de cálculo de matrices de dependencia estadística entre variables objetivo.

Permite evaluar la fuerza de asociación mutua entre múltiples objetivos (*targets*) de manera 
simétrica e indexada. Aplica coeficientes estadísticos condicionados por el tipo técnico de los datos: 
V de Cramer para pares categóricos, correlación de Spearman para numéricos y Eta cuadrado corregido 
para relaciones mixtas, además de computar umbrales adaptativos de corte.
"""

import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, spearmanr, kruskal

def compute_target_dependency_matrix(df, targets, col_types):
    """
    Construye de forma triangular simétrica la matriz de dependencia para los objetivos.
    
    Determina la fuerza de la relación de cada par de objetivos ($t_1, t_2$) evaluando sus niveles 
    técnicos. Si el nivel técnico se encuentra en [1, 2] se asume un comportamiento categórico, 
    mientras que valores en [3, 4] se procesan como continuos o discretos, aplicando filtros de 
    umbral mínimo (*soft thresholds*) para mitigar ruidos estadísticos.
    """
    # 1. Inicialización en 1.0 según el documento base (Pág. 15)
    matrix = pd.DataFrame(1.0, index=targets, columns=targets)
    
    # 2. Bucle indexado de forma triangular simétrica estricto (Pág. 15)
    for i, t1 in enumerate(targets):
        for t2 in targets[i+1:]:
            
            # Obtención limpia del nivel técnico desde la metadata del dossier
            type1 = col_types.get(t1).get('technical_level') if isinstance(col_types.get(t1), dict) else col_types.get(t1)
            type2 = col_types.get(t2).get('technical_level') if isinstance(col_types.get(t2), dict) else col_types.get(t2)
            
            score = 0.0

            # CASO A: Ambos son categóricos (Pág. 15)
            if type1 in [1, 2] and type2 in [1, 2]:
                score = calculate_cramers_v(df[t1], df[t2])
                if score < 0.10: score = 0.0

            # CASO B: Ambos son numéricos (Pág. 16 - Correlación de Spearman)
            elif type1 in [3, 4] and type2 in [3, 4]:
                res = spearmanr(df[t1], df[t2])
                coef = res.statistic if hasattr(res, 'statistic') else res[0]
                score = abs(coef) if not pd.isna(coef) else 0.0
                if score < 0.30: score = 0.0

            # CASO C: Mixto (Pág. 16 - Razón de Correlación Eta al cuadrado)
            else:
                if type1 in [1, 2]:
                    cat_col, num_col = t1, t2
                else:
                    cat_col, num_col = t2, t1
                score = calculate_eta_squared(df, cat_col, num_col)
                if score < 0.06: score = 0.0

            # Asignación simétrica de la celda evaluada
            matrix.loc[t1, t2] = round(score, 4)
            matrix.loc[t2, t1] = round(score, 4)
            
    return matrix

def calculate_cramers_v(x, y) -> float:
    """
    Calcula el coeficiente V de Cramer para medir la asociación entre dos variables nominales.
    
    Construye la tabla de contingencia y computa el estadístico Chi-cuadrado para derivar un valor 
    normalizado en el rango $[0, 1]$, donde $0$ representa independencia absoluta y $1$ asociación perfecta.
    """
    tabla = pd.crosstab(x, y)     
    if tabla.empty: return 0.0
    r, c  = tabla.shape     
    if r <= 1 or c <= 1: return 0.0
        
    chi2, _, _, _ = chi2_contingency(tabla)
    n = tabla.sum().sum()     
    if n == 0: return 0.0
    phi2 = chi2 / n     
    denom = min(r - 1, c - 1)
    return np.sqrt(phi2 / denom) if denom > 0 else 0.0

def calculate_eta_squared(df, cat_col, num_col) -> float:
    """
    Calcula la razón de correlación Eta al cuadrado ($\eta^2$) mediante una aproximación no paramétrica.
    
    Emplea la prueba de Kruskal-Wallis como alternativa robusta para evaluar la variabilidad de la 
    variable numérica entre los grupos de la variable categórica, determinando la fracción de varianza 
    explicada de manera acotada.
    """
    temp_df = df[[cat_col, num_col]].copy()
    temp_df[num_col] = pd.to_numeric(temp_df[num_col], errors='coerce')

    temp_df = temp_df.dropna(subset=[num_col])
    temp_df = temp_df[temp_df[cat_col].astype(str).str.strip() != ""]

    if temp_df.empty: return 0.0
    
    groups = [group[num_col].values for name, group in temp_df.groupby(cat_col)]
    groups = [g for g in groups if len(g) > 0]
    if len(groups) < 2: return 0.0

    try:
        h_stat, _ = kruskal(*groups)
        n = len(temp_df)
        if n <= 1: return 0.0  

        eta_sq = h_stat / (n - 1)
        return max(0.0, min(float(eta_sq), 1.0))
    except Exception:
        return 0.0

def compute_threshold(matrix: pd.DataFrame, threshold_cfg) -> float:
    """
    Calcula el umbral de corte para discriminar dependencias significativas en la matriz.
    
    Si se configura como `'auto'`, establece el límite dinámicamente aislando la diagonal principal 
    y computando la suma de la mediana más la desviación estándar de las puntuaciones de asociación extraídas.
    """
    scores = matrix.values[~np.eye(len(matrix), dtype=bool)] 
    if len(scores) == 0: return 0.10
    if threshold_cfg == 'auto':   
        return float(np.median(scores) + np.std(scores))
    return float(threshold_cfg)