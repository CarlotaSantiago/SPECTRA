import pandas as pd
from spacy.lang.es.stop_words import STOP_WORDS
import io
import os

# 1. Configuración de Stopwords
descartar = {'no', 'sin', 'ni'}
stop_word = STOP_WORDS - descartar

def quitar_stopwords(col):
    return (col.fillna('')
            .str.lower()
            .str.split()
            # Unimos las palabras de nuevo con espacios para que sea texto, no una lista
            .apply(lambda x: " ".join([word for word in x if word not in stop_word])))

def limpiar_datos(data_serie):
    acentos = str.maketrans('áéíóúÁÉÍÓÚ', 'aeiouAEIOU')
    # Limpieza de caracteres y acentos
    data = data_serie.astype(str).str.lower()\
        .str.replace(r'[^\w\s]', '', regex=True)\
        .str.translate(acentos)
    # Quitar las stopwords
    data = quitar_stopwords(data)
    return data

async def procesar_archivo(upload_file, aplicar_limpieza: bool):
    # Asegurar que la carpeta de destino existe
    os.makedirs("uploads", exist_ok=True)
    
    content = await upload_file.read()
    
    # Lectura del archivo
    if upload_file.filename.endswith('.xlsx') or upload_file.filename.endswith('.xls'):
        df = pd.read_excel(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))

    # 2. Aplicar lógica de limpieza
    if aplicar_limpieza:
        columnas_a_limpiar = ['datosclini', 'sospechadiag']
        for col in columnas_a_limpiar:
            if col in df.columns:
                # IMPORTANTE: Llamamos a limpiar_datos (el nombre correcto)
                df[col] = limpiar_datos(df[col])

    # 3. Guardar el resultado
    output_filename = f"procesado_{upload_file.filename}"
    # Si el original era CSV, lo convertimos a XLSX para mantener el formato de Excel
    if not output_filename.endswith('.xlsx'):
        output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
        
    output_path = os.path.join("uploads", output_filename)
    df.to_excel(output_path, index=False)
    
    return {
        "filename": upload_file.filename, 
        "path": output_path, 
        "rows": len(df),
        "message": "Archivo preprocesado y guardado con éxito"
    }