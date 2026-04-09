import re
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from scipy.sparse import hstack, issparse
from sklearn.naive_bayes import GaussianNB
from scipy.stats import randint, loguniform
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_selection import mutual_info_classif, SelectKBest
from sklearn.metrics import accuracy_score, confusion_matrix, cohen_kappa_score,  recall_score, ConfusionMatrixDisplay, make_scorer, precision_score, f1_score


kappa_score = make_scorer(cohen_kappa_score)
recall_scorer = make_scorer(recall_score)

modelos_binarios = [
    'random_forest',
    'svm',
    'naive_bayes',
    'mlp'
]

parametresDT = {
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': randint(2, 11)
}

parametresGB = {
    'n_estimators': [100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 10]
}

parametresRFC = {
    'n_estimators': randint(100, 300),
    'max_depth': randint(10, 30),
    'min_samples_split': randint(2, 11),
    'min_samples_leaf': randint(1, 11),
    'max_features': ['sqrt', 'log2']
}

parametresSVM = {
    'C': loguniform(1e-3, 1e3),
    'kernel': ['linear', 'rbf', 'poly'],
    'gamma': ['scale']
}

parametresNB = {
    'var_smoothing': loguniform(1e-12, 1e-4)
}

parametresMLP = {
    'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
    'activation': ['relu'],
    'solver': ['adam'],
    'alpha': [0.0001, 0.001, 0.01, 0.1],
    'learning_rate': ['adaptive'],
    'early_stopping': [True],
    'max_iter': [200, 300]
}

BASE_DIR = os.getcwd()
DATA_PATH = os.path.join(BASE_DIR, "uploads")
MODELS_PATH = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_PATH, exist_ok=True)


def marcar_especialidad(text):
    """
    Marca la especialidad basada en el texto proporcionado.
    Retorna 0 si el texto contiene 'CUELLO', 'MAMA' o 'ESCROTO', de lo contrario retorna 1.
    """
    if re.search(r'CUELLO|MAMA|ESCROTO', str(text)):
        return 0
    else:
        return 1

def marcar_sala(text):
    """
    Marca si la sala es HOMBRO basándose en el texto proporcionado.
    Retorna 1 si el texto contiene 'HOMBRO', de lo contrario retorna 0.
    """
    if re.search(r'HOMBRO', str(text)):
        return 1

    return 0

def marcar_prioridad_binaria(text, caso1):
    """
    Marca la prioridad binaria basada en el texto proporcionado.
    Retorna 1 si el texto coincide con caso1, de lo contrario retorna 0.
    """
    if caso1 == text:
        return 1

    return 0

def marcar_prioridad_terciaria(text):
    """
    Marca la prioridad terciaria basada en el texto proporcionado.
    Retorna 0 si el texto es 'A', 1 si el texto es 'B', y 2 para cualquier otro caso.
    """
    if text == 'A':
        return 0
    elif text == 'B':
        return 1

    return 2


def concatenar_archivos(filenames: list):
    """
    Carga y concatena los archivos Excel proporcionados en una sola DataFrame.
    """
    all_data = []
    for f in filenames:
        path = os.path.join(DATA_PATH, f)
        if os.path.exists(path):
            df = pd.read_excel(path)
            all_data.append(df)

    if not all_data:
        return pd.DataFrame()  # Retorna un DataFrame vacío si no hay datos

    data = pd.concat(all_data, ignore_index=True)
    data.replace(['None', 'NaN', 'nan'], np.nan, inplace=True)
    data.dropna(inplace=True)

    return data


async def entrenar_modelos_prioridad(
        filenames: list,
        model_key: str,
        target_column: str):
    """
    Entrena modelos de prioridad (binarios en cascada o terciarios).

    Args:
        filenames: Lista de archivos Excel con los datos de entrenamiento.
        model_key: Clave del modelo a entrenar ('random_forest', 'svm', etc.).
        target_column: Columna objetivo para el scaler.

    Returns:
        Diccionario con el estado del entrenamiento y resultados.
    """
    data = concatenar_archivos(filenames)
    if data.empty:
        return {"error": "No hay datos para entrenar"}

    data['texto'] = data['datosclini'].astype(str) + " " + data['sospechadiag'].astype(str)

    # --- PROCESAMIENTO DE EDAD (Común para ambos) ---
    scaler = StandardScaler()
    data['edad_scaled'] = scaler.fit_transform(data[['edad']])
    joblib.dump(scaler, os.path.join(MODELS_PATH, f"scaler_{target_column}.pkl"))

    # --- DICCIONARIO DE ALGORITMOS ---
    algorithms = {
        'random_forest': (RandomForestClassifier(), parametresRFC),
        'svm': (SVC(), parametresSVM),
        'naive_bayes': (GaussianNB(), parametresNB),
        'mlp': (MLPClassifier(), parametresMLP),
        'decision_tree': (DecisionTreeClassifier(), parametresDT),
        'gradient_boosting': (GradientBoostingClassifier(), parametresGB),
        'random_forest_multi': (RandomForestClassifier(), parametresRFC)
    }

    data['prioridad'] = data['observ'].astype(str).str.strip().str[0]

    if model_key not in algorithms:
        return {"error": "Modelo no soportado"}

    # ---------------------------------------------------------
    # FLUJO 1: MODELOS BINARIOS EN CASCADA
    # ---------------------------------------------------------
    if model_key in modelos_binarios:
        # --- NIVEL 1: A vs (B y C) ---
        data['y_c1'] = data['prioridad'].apply(lambda x: marcar_prioridad_binaria(x, 'A'))
        res_c1 = await ejecutar_entrenamiento(
            data,
            model_key,
            algorithms[model_key],
            f"{target_column}_C1",
            target_column,
            'y_c1')

        # --- NIVEL 2: B vs C (Solo con los que no son A) ---
        data_c2 = data[data['prioridad'] != 'A'].copy()
        if not data_c2.empty:
            data_c2['y_c2'] = data_c2['prioridad'].apply(lambda x: marcar_prioridad_binaria(x, 'B'))
            res_c2 = await ejecutar_entrenamiento(
                data_c2,
                model_key,
                algorithms[model_key],
                f"{target_column}_C2",
                target_column,
                'y_c2')

            return {"status": "cascada_completa", "paso1": res_c1, "paso2": res_c2}

        return {"status": "paso1_completado", "info": "No había suficientes datos B/C para el paso 2"}

    # ---------------------------------------------------------
    # FLUJO 2: MODELO TERCIARIO (DIRECTO)
    # ---------------------------------------------------------
    else:
        data['y_multi'] = data['prioridad'].apply(marcar_prioridad_terciaria)
        resultado = await ejecutar_entrenamiento(
            data, 
            model_key, 
            algorithms[model_key],
            f"{target_column}",
            target_column,
            'y_multi')
        return resultado

# --- FUNCIÓN AUXILIAR DE APOYO PARA NO REPETIR CÓDIGO ---
async def ejecutar_entrenamiento(
    df,
    model_key,
    model_info,
    save_name,
    target_column,
    target_col_name
):
    """
    Ejecuta el entrenamiento de un modelo con búsqueda de hiperparámetros.

    Args:
        df: DataFrame con los datos de entrenamiento.
        model_key: Clave del modelo a entrenar.
        model_info: Tupla con (modelo, distribución de parámetros).
        save_name: Nombre para guardar el modelo.
        target_column: Columna objetivo.
        target_col_name: Nombre de la columna objetivo en el DataFrame.

    Returns:
        Diccionario con el nombre del modelo y los mejores parámetros.
    """
    y = df[target_col_name]
    model_obj, param_dist = model_info

    nombre_kbest = f"kbest_{save_name}.pkl"
    nombre_vectorizer = f"vectorizer_{save_name}.pkl"
    path_kbest = os.path.join(MODELS_PATH, nombre_kbest)
    path_vectorizer = os.path.join(MODELS_PATH, nombre_vectorizer)

    if os.path.exists(path_kbest) and os.path.exists(path_vectorizer):
        vectorizer = joblib.load(path_vectorizer)
        kbest = joblib.load(path_kbest)
        x_vec = vectorizer.transform(df['texto'])
        x_text = kbest.transform(x_vec)
    else:
        vectorizer = CountVectorizer(analyzer='word', ngram_range=(1, 2))
        x_vec = vectorizer.fit_transform(df['texto'])
        kbest = SelectKBest(mutual_info_classif, k=7500)
        x_text = kbest.fit_transform(x_vec, y)

        joblib.dump(vectorizer, os.path.join(MODELS_PATH, f"vectorizer_{save_name}.pkl"))
        joblib.dump(kbest, os.path.join(MODELS_PATH, f"kbest_{save_name}.pkl"))


    # Unir con Edad
    edad_col = df[['edad_scaled']].values
    x_final = hstack([x_text, edad_col]) if issparse(x_text) else np.hstack([x_text, edad_col])

    # Entrenamiento
    x_train = x_final.toarray() if model_key == 'naive_bayes' else x_final
    search = RandomizedSearchCV(
        model_obj,
        param_distributions=param_dist,
        n_iter=10,
        scoring=kappa_score,
        cv=10,
        n_jobs=-1,
        random_state=42)

    search.fit(x_train, y)

    joblib.dump(search.best_estimator_, os.path.join(MODELS_PATH, f"{model_key}_{save_name}.pkl"))
    return {"model": save_name, "best_params": search.best_params_}

async def entrenar_modelos_binarios(filenames: list, model_key: str, target_column: str):
    """
    Entrena el modelo seleccionado usando los archivos proporcionados.
    target_column: 'etiqueta_mio', 'etiqueta_hombro' o 'etiqueta_prioridad'
    """
    # 1. Cargar y concatenar todos los archivos seleccionados
    all_data = []
    for f in filenames:
        path = os.path.join(DATA_PATH, f)
        if os.path.exists(path):
            df = pd.read_excel(path)
            all_data.append(df)

    if not all_data:
        return {"error": "No hay datos para entrenar"}

    data = pd.concat(all_data, ignore_index=True)
    data.replace(['None', 'NaN', 'nan'], np.nan, inplace=True)
    data.dropna(inplace=True)
    data['texto'] = data['datosclini'] + " " + data['sospechadiag']

    if target_column == "mio":
        data['entrenar'] = data['desprest'].apply(marcar_especialidad)
    elif target_column == "hombro":
        data['entrenar'] = data['desprest'].apply(marcar_sala)
    else:
        data['entrenar'] = data['desprest'].apply(marcar_prioridad_terciaria)

    y = data['entrenar']
    nombre_kbest = f"kbest_{target_column}.pkl"
    nombre_vectorizer = f"vectorizer_{target_column}.pkl"
    path_kbest = os.path.join(MODELS_PATH, nombre_kbest)
    path_vectorizer = os.path.join(MODELS_PATH, nombre_vectorizer)

    if os.path.exists(path_kbest) and os.path.exists(path_vectorizer):
        vectorizer = joblib.load(path_vectorizer)
        kbest = joblib.load(path_kbest)
        x = vectorizer.transform(data['texto'])
        x_selected = kbest.transform(x)
    else:
        vectorizer = CountVectorizer(analyzer='word', ngram_range=(1, 2))
        x = vectorizer.fit_transform(data['texto'])
        kbest = SelectKBest(mutual_info_classif, k=7500)
        x_selected = kbest.fit_transform(x, y)
        joblib.dump(vectorizer, os.path.join(MODELS_PATH, f"vectorizer_{target_column}.pkl"))
        joblib.dump(kbest, os.path.join(MODELS_PATH, f"kbest_{target_column}.pkl"))


    algorithms = {
        'random_forest': (RandomForestClassifier(), parametresRFC),
        'svm': (SVC(), parametresSVM),
        'naive_bayes': (GaussianNB(), parametresNB),
        'mlp': (MLPClassifier(), parametresMLP),
    }

    if model_key in algorithms:
        model, param_dist = algorithms[model_key]

        # Preparar datos: Naive Bayes necesita array denso, los demás no
        x_train = x_selected.toarray() if model_key == 'naive_bayes' else x_selected

        # 4. Búsqueda de los mejores hiperparámetros
        random_search = RandomizedSearchCV(
            model, 
            param_distributions=param_dist, 
            n_iter=10, # Bajado a 10 para que no tarde una eternidad en el servidor
            scoring=kappa_score,
            cv=10, # Bajado a 3 para agilizar el proceso web
            verbose=2,
            n_jobs=-1, 
            random_state=42
        )
        random_search.fit(x_train, y)
        # 5. Guardar el mejor modelo resultante
        best_model = random_search.best_estimator_
        # Usar path absoluto para asegurar el guardado
        file_path = os.path.abspath(os.path.join(MODELS_PATH, f"{model_key}_{target_column}.pkl"))

        joblib.dump(best_model, file_path)
        return {"status": "trained", "best_params": random_search.best_params_}

    return {"error": "Modelo no soportado"}