import pandas as pd
import numpy as np
 
def stratified_sample_100(
        df: pd.DataFrame,
        target_cols: list[str],
        n: int = 100) -> pd.DataFrame:
    """ 
    Muestrea exactamente `n` filas con estratificación proporcional. 
    Soporta uno o múltiples targets mediante columna combinada 
    temporal. 
    Usa Largest Remainder para garantizar que sum(asignaciones) == n 
    exacto. 
    """

    # 1. Columna de estratificación 
    if len(target_cols) == 1: 
        strata_col = target_cols[0] 
    else: 
        # Columna combinada temporal (no se incluye en el output) 
        df = df.copy() 
        df["_strata"] = df[target_cols].astype(str).agg("_".join, axis=1) 
        strata_col = "_strata" 
 
    # 2. Calcular tamaño exacto de cada grupo 
    group_sizes = df.groupby(strata_col).size() 
    total_rows = len(df) 
     
    # Cuotas reales (flotantes) 
    exact_quotas = group_sizes / total_rows * n 
     
    # 3. Largest Remainder Method 
    # Sustituimos .floor() por np.floor sobre los valores
    floor_quotas = np.floor(exact_quotas.values).astype(int)
    
    # Creamos una serie con esos valores para mantener los índices (nombres de los grupos)
    floor_quotas = pd.Series(floor_quotas, index=exact_quotas.index)
    
    remainders = exact_quotas - floor_quotas
 
    deficit = int(n - floor_quotas.sum())  # Cuántas filas faltan para llegar a n 
     
    if deficit > 0:
        # Asignar las filas restantes a los grupos con mayor residuo
        top_remainder_groups = remainders.nlargest(deficit).index 
        for group in top_remainder_groups:
            floor_quotas.at[group] += 1 
     
    # Garantía: cada grupo tiene al menos 1 fila (comentado en el original)
    #floor_quotas = floor_quotas.clip(lower=1)
    
    # 4. Muestreo por grupo 
    sampled_parts = [] 
    for group_value, group_df in df.groupby(strata_col): 
        k = floor_quotas[group_value] 
        k = min(k, len(group_df))  # no pedir más filas de las que hay 
        sampled_parts.append(group_df.sample(n=k, random_state=42)) 
     
    result = pd.concat(sampled_parts) 
     
    # 5. Limpiar columna temporal 
    if "_strata" in result.columns: 
        result = result.drop(columns=["_strata"]) 
     
    return result
