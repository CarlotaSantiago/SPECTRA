import os
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack

BASE_DIR = os.getcwd()
DATA_PATH = os.path.join(BASE_DIR, "uploads")
MODELS_PATH = os.path.join(BASE_DIR, "models")

modelos_binarios = ['random_forest', 'svm', 'naive_bayes', 'mlp']

def concatenar_archivos(filenames: list):
    """Combina múltiples archivos Excel en un único DataFrame.
    
    Args:
        filenames: Lista de nombres de archivos a procesar
    
    Returns:
        DataFrame con los datos combinados y limpios
    """
    all_data = []

    for f in filenames:
        path = os.path.join(DATA_PATH, f)
        if os.path.exists(path):
            df = pd.read_excel(path)
            all_data.append(df)

    if not all_data:
        return pd.DataFrame()

    data = pd.concat(all_data, ignore_index=True)
    data.replace(['None', 'NaN', 'nan'], np.nan, inplace=True)
    data.dropna(subset=['datosclini', 'sospechadiag', 'edad'], inplace=True)

    return data

async def predecir_final(model_key: str, filenames: list, target_col: str):
    """Realiza predicciones usando modelos entrenados para el target especificado.
    
    Args:
        model_key: Clave del modelo a usar ('random_forest', 'svm', 'naive_bayes', 'mlp')
        filenames: Lista de archivos Excel con los datos a predecir
        target_col: Columna objetivo ('prioridad', 'mio', 'hombro')
    
    Returns:
        Dict con las predicciones y confianzas, o error si falla
    """
    # 1. Preparación
    data = concatenar_archivos(filenames)
    if data.empty:
        return {"error": "No hay datos"}

    data['texto'] = data['datosclini'].astype(str) + " " + data['sospechadiag'].astype(str)

    # 2. Scaler de Edad
    scaler_path = os.path.join(MODELS_PATH, f"scaler_{target_col}.pkl")

    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        data['edad_scaled'] = scaler.transform(data[['edad']])

    # --- FUNCIÓN INTERNA CON PROBABILIDADES ---
    def ejecutar_inferencia(data_subset, nombre_fichero_base):
        v_path = os.path.join(MODELS_PATH, f"vectorizer_{nombre_fichero_base}.pkl")
        k_path = os.path.join(MODELS_PATH, f"kbest_{nombre_fichero_base}.pkl")
        m_path = os.path.join(MODELS_PATH, f"{model_key}_{nombre_fichero_base}.pkl")

        if not all(os.path.exists(p) for p in [v_path, k_path, m_path]): return None

        v, k, m = joblib.load(v_path), joblib.load(k_path), joblib.load(m_path)

        x_f = k.transform(v.transform(data_subset['texto']))
        if 'edad_scaled' in data_subset.columns:
            x_f = hstack([x_f, data_subset[['edad_scaled']].values])
        if model_key == 'naive_bayes': 
            x_f = x_f.toarray()

        preds = m.predict(x_f)

        try:
            probs = m.predict_proba(x_f)
            confianzas = [round(np.max(p) * 100, 2) for p in probs]
        except Exception:
            confianzas = [None] * len(preds)

        return preds, confianzas

    def get_label(val, col):
        """Convierte valor numérico a etiqueta según el target."""
        if col == "mio":
            return "MIO" if val == 0 else "NO MIO"

        if col == "hombro":
            return "HOMBRO" if val == 1 else "NO HOMBRO"

        return {0: 'A', 1: 'B', 2: 'C'}.get(val, val)

    def format_confianza(c):

        return f"{c}%" if c else "N/A"

    # 3. Lógica de Respuesta
    try:
        es_prioridad_binario = target_col == "prioridad" and model_key in modelos_binarios

        if es_prioridad_binario:
            res_c1 = ejecutar_inferencia(data, f"{target_col}_C1")
            if res_c1 is None: return {"error": "Faltan modelos C1"}
            preds_c1, confs_c1 = res_c1

            final_res = []
            for i, p in enumerate(preds_c1):
                if p == 1:
                    final_res.append({"label": "A", "confianza": f"{confs_c1[i]}%"})
                else:
                    fila = data.iloc[[i]]
                    preds_c2, confs_c2 = ejecutar_inferencia(fila, f"{target_col}_C2")
                    label = "B" if preds_c2[0] == 1 else "C"
                    final_res.append({"label": label, "confianza": f"{confs_c2[0]}%"})
            return {"status": "success", "tipo": "cascada", "predicciones": final_res}

        res = ejecutar_inferencia(data, target_col)
        if res is None:
            return {"error": "Modelos no encontrados"}
        preds, confs = res

        final_res = [
            {"label": get_label(p, target_col), "confianza": format_confianza(c)}
            for p, c in zip(preds, confs)
        ]

        return {"status": "success", "tipo": "simple", "predicciones": final_res}

    except Exception as e:
        return {"error": str(e)}