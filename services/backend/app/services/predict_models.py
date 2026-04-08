import os
import joblib
import pandas as pd
import numpy as np
from scipy.sparse import issparse

MODELS_PATH = "./models"
DATA_PATH = "./preprocessed"

def predecir_con_modelos(model_key: str, filenames: list, target_col: str):
    """
    Carga los archivos, los concatena y predice el resultado final como un single block.
    """
    print(f"Prediciendo con modelo {model_key} para {target_col} usando archivos: {filenames}")
    # 1. Definir rutas de los componentes del modelo
    model_file = os.path.join(MODELS_PATH, f"{model_key}_{target_col}.pkl")
    vectorizer_file = os.path.join(MODELS_PATH, f"vectorizer_{target_col}.pkl")
    kbest_file = os.path.join(MODELS_PATH, f"kbest_{target_col}.pkl")
    print(f"Rutas de modelos: {model_file}, {vectorizer_file}, {kbest_file}")
    # Verificación de existencia
    if not all(os.path.exists(p) for p in [model_file, vectorizer_file, kbest_file]):
        return {"error": "Modelos no encontrados. Por favor, entrena primero."}
    print("Modelos encontrados, procediendo con la predicción...")
    try:
        # 2. Cargar y CONCATENAR los documentos (Igual que en el entrenamiento)
        all_data = []
        for f in filenames:
            path = os.path.join(DATA_PATH, f)
            if os.path.exists(path):
                df = pd.read_excel(path)
                # Opcional: añadir una columna para saber de qué archivo venía cada fila
                df['archivo_origen'] = f
                all_data.append(df)
        print(f"Archivos cargados: {len(all_data)}. Filas por archivo: {[len(df) for df in all_data]}")
        if not all_data:
            return {"error": "No se encontraron los archivos de datos."}

        # Creamos un único DataFrame
        data_total = pd.concat(all_data, ignore_index=True)
        print(f"Datos concatenados para predicción: {data_total.shape[0]} filas, {data_total.shape[1]} columnas")
        # 3. Preparación del texto (mismo formato que el entrenamiento)
        # Importante: No borramos filas aquí para no perder el orden del Excel original
        data_total['texto_final'] = (
            data_total['datosclini'].fillna('') + " " + data_total['sospechadiag'].fillna('')
        )

        # 4. Cargar transformadores y modelo
        vectorizer = joblib.load(vectorizer_file)
        kbest = joblib.load(kbest_file)
        model = joblib.load(model_file) # Asegúrate de cargar el best_model guardado
        print("Modelos cargados correctamente, realizando transformaciones y predicción...")
        # 5. Transformación y Predicción
        X_vec = vectorizer.transform(data_total['texto_final'])
        X_selected = kbest.transform(X_vec)
        print(f"Transformaciones completas: {X_vec.shape} -> {X_selected.shape}")
        if issparse(X_selected):
            try:
                X_selected = X_selected.toarray()
            except: pass

        # Realizamos la predicción de todo el bloque junto
        predicciones = model.predict(X_selected)
        print(f"Predicción completa para {len(predicciones)} filas")
        # 6. Preparar la respuesta
        # Devolvemos una lista de resultados que el frontend pueda mapear
        return {
            "status": "success",
            "total_filas": len(data_total),
            "predicciones": predicciones.tolist(),
            # Opcional: puedes devolver info extra para la tabla del frontend
            "indices": data_total.index.tolist() 
        }

    except Exception as e:
        return {"error": f"Error en la predicción concatenada: {str(e)}"}