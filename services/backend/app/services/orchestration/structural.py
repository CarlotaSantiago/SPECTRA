import pandas as pd

def detect_structural_absences(df: pd.DataFrame, targets: list[str], umbral: float = 0.95) -> dict | None:     
    # Detección limpia de ausencias estructurales (MNAR)
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
