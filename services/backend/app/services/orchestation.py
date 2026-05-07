import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, spearmanr, kruskal
import itertools
from app.services.classify import classify_data, compute_information_gain, compute_information_gain_targets, encode_series

def compute_target_dependency_matrix(df, targets, col_types):
    # Crear matriz vacía de tamaño [targets x targets], inicializada a 0
    # Usamos un DataFrame para que sea visualmente claro y fácil de indexar
    matrix = pd.DataFrame(0.0, index=targets, columns=targets)

    # PARA CADA par (t1, t2) en todas las combinaciones posibles de targets
    for t1, t2 in itertools.permutations(targets, 2):
        
        # NUEVO ENFOQUE: USAR INFORMATION GAIN NORMALIZADO
        temp_df = df[[t1, t2]].dropna()
        if temp_df.empty:
            continue

        t1_discrete = col_types.get(t1) in [1, 2]
        t2_discrete = col_types.get(t2) in [1, 2]

        try:
            if t2_discrete:
                # t1 -> t2 (t2 es el target)
                score = compute_information_gain_targets(df, t1, t2, col_types, t1_discrete, device=None)
            else:
                # t1 -> t2 (t2 es el target)
                score = compute_information_gain_targets(df, t1, t2, col_types, t1_discrete, device=None)
            matrix.loc[t1, t2] = round(score, 4)

        except Exception as e:
            print(f"Error al calcular dependencia entre {t1} y {t2}: {e}")

            # type1 = col_types.get(t1)
            # type2 = col_types.get(t2)
            # score = 0.0

            # # CASO A: Ambos son categóricos
            # if type1 in [1,2] and type2 in [1,2]:
            #     score = calculate_cramers_v(df[t1], df[t2])

            # # CASO B: Ambos son numéricos
            # elif type1 in [3,4] and type2 in [3,4]:
            #     coef, _ = spearmanr(df[t1], df[t2])
            #     score = abs(coef)  # score ∈ [0, 1]

            # # CASO C: Mixto (uno categórico y otro numérico)
            # else:
            #     if type1 in [1, 2]:
            #         cat_col, num_col = t1, t2
            #     else:
            #         cat_col, num_col = t2, t1
            #     score = calculate_eta_squared(df, cat_col, num_col)
            # # Guardar score en matrix[t1][t2] y matrix[t2][t1] ← es simétrica
            # matrix.loc[t1, t2] = round(score, 4)
            # matrix.loc[t2, t1] = round(score, 4)
    # Rellenar diagonal con 1.0
    for t in targets:
        matrix.loc[t, t] = 1.0

    return matrix

# --- FUNCIONES AUXILIARES DE NORMALIZACIÓN ---

# def calculate_cramers_v(x, y):
#     confusion_matrix = pd.crosstab(x, y)
#     if confusion_matrix.empty: return 0.0
#     chi2 = chi2_contingency(confusion_matrix)[0]
#     n = confusion_matrix.sum().sum()
#     r, k = confusion_matrix.shape
#     return np.sqrt(chi2 / (n * min(r-1, k-1))) if n > 0 and min(r-1, k-1) > 0 else 0.0

# def calculate_eta_squared(df, cat_col, num_col):
#     # 1. Creamos una copia local solo con las columnas necesarias
#     # 2. Forzamos la columna numérica a serlo (convirtiendo "" en NaN)
#     temp_df = df[[cat_col, num_col]].copy()
#     temp_df[num_col] = pd.to_numeric(temp_df[num_col], errors='coerce')
    
#     # 3. Eliminamos filas donde el número o la categoría sean nulos/vacíos
#     # (El fillna("") previo se convierte aquí en NaN gracias a pd.to_numeric)
#     temp_df = temp_df.dropna(subset=[num_col])
#     temp_df = temp_df[temp_df[cat_col].astype(str).str.strip() != ""]

#     # 4. Agrupamos
#     groups = [group[num_col].values for name, group in temp_df.groupby(cat_col)]
    
#     # Validaciones de seguridad
#     if len(groups) < 2: 
#         return 0.0
    
#     # Verificamos que todos los grupos tengan al menos un valor
#     groups = [g for g in groups if len(g) > 0]
#     if len(groups) < 2:
#         return 0.0

#     try:
#         # Kruskal-Wallis H-test
#         h_stat, _ = kruskal(*groups)
        
#         # Eta² normalizado: (H - k + 1) / (n - k)
#         n = len(temp_df)
#         k = len(groups)
        
#         if n == k: return 0.0 # Evitar división por cero
        
#         eta_sq = (h_stat - k + 1) / (n - k)
#         return max(0.0, min(float(eta_sq), 1.0)) 
    
#     except Exception as e:
#         print(f"Error en Kruskal-Wallis entre {cat_col} y {num_col}: {e}")
#         return 0.0
    
def resolve_chain_order(dependency_matrix, threshold):
    """
    Calcula qué target tiene más peso/influencia sobre los demás
    para determinar quién va primero en la cadena.
    """
    influence_scores = {}
    targets = dependency_matrix.columns.tolist()

    for t in targets:
        # Sumamos los scores de la fila de 't', pero:
        # 1. Ignoramos la diagonal (donde t == t, que es 1.0)
        # 2. Ignoramos scores por debajo del threshold
        row_scores = dependency_matrix.loc[t]
        
        # Filtramos la diagonal y el umbral
        filtered_scores = [
            score for label, score in row_scores.items() 
            if label != t and score >= threshold
        ]
        
        influence_scores[t] = sum(filtered_scores)

    # Ordenar targets de MAYOR a MENOR influence_score
    # En caso de empate, Python mantiene el orden original
    sorted_order = sorted(influence_scores, key=influence_scores.get, reverse=True)
    
    return sorted_order

def build_chain_strategy(dependency_matrix, col_types, threshold=0.15):
    """
    Decide la arquitectura final del modelo y el orden de ejecución.
    """
    # Extraer valores fuera de la diagonal para encontrar la dependencia máxima
    targets = dependency_matrix.columns.tolist()
    mask = ~np.eye(dependency_matrix.shape[0], dtype=bool)
    max_dependency = dependency_matrix.values[mask].max()
    # SI la dependencia máxima es muy baja, no merece la pena encadenar
    if max_dependency < threshold:
        return {
            "strategy": "MultiOutput",
            "order": targets,
            "max_dependency": f"Baja dependencia detectada (max: {max_dependency})"
        }

    # Obtener el orden óptimo
    order = resolve_chain_order(dependency_matrix, threshold)
    # Determinar el tipo de cadena basado en los col_types de los targets
    target_types = [col_types.get(t) for t in order]
    if all(t_type in [1, 2] for t_type in target_types):
        strategy = "ClassifierChain"
    elif all(t_type in [3, 4] for t_type in target_types):
        strategy = "RegressorChain"
    else:
        strategy = "HybridChain"

    return {
        "strategy": strategy,
        "order": order,
        "max_dependency": max_dependency
    }