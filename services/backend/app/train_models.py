import pandas as pd
import numpy as np
import re
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_selection import mutual_info_classif, SelectKBest

from sklearn.ensemble import RandomForestClassifier 
from sklearn.ensemble import RandomForestClassifier  # o el clasificador que esté usando

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier


from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix, cohen_kappa_score,  recall_score, ConfusionMatrixDisplay, make_scorer, precision_score, f1_score
from scipy.stats import randint, loguniform

import joblib

kappa_score = make_scorer(cohen_kappa_score)
recall_scorer = make_scorer(recall_score)

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

DATA_PATH = "./preprocessed"
MODELS_PATH = "./models"
os.makedirs(MODELS_PATH, exist_ok=True)


def marcar_especialidad(text):
    if re.search(r'CUELLO|MAMA|ESCROTO', str(text)):
        return 0
    else:
        return 1

def marcar_sala(text):
    if re.search(r'HOMBRO', str(text)):
        return 1
    else:
        return 0

def marcar_prioridad(text):
    if re.search(r'ALTA', str(text)):
        return 1
    else:
        return 0  

async def entrenar_modelos(filenames: list, model_key: str, target_column: str):
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

    if target_column == "etiqueta_mio":
        data['entrenar'] = data['desprest'].apply(marcar_especialidad)
    elif target_column == "etiqueta_hombro":
        data['entrenar'] = data['desprest'].apply(marcar_sala)
    else:
        data['entrenar'] = data['desprest'].apply(marcar_prioridad)


    vectorizer = CountVectorizer(analyzer='word', ngram_range=(1, 2))
    x = vectorizer.fit_transform(data['texto'])
    y = data['entrenar']

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
        print(f"Buscando mejores parámetros para {model_key}...")
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
        joblib.dump(best_model, os.path.join(MODELS_PATH, f"{model_key}_{target_column}.pkl"))
        
        return {"status": "trained", "best_params": random_search.best_params_}

    return {"error": "Modelo no soportado"}