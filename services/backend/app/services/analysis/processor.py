"""
Módulo de preprocesamiento y limpieza de texto en español.

Permite normalizar series de datos textuales eliminando caracteres especiales, 
acentos y palabras vacías (stopwords), manteniendo términos clave para preservar 
el contexto de negación en tareas de procesamiento de lenguaje natural (PLN).
"""

from spacy.lang.es.stop_words import STOP_WORDS


# 1. Configuración de Stopwords
# Conservamos palabras de negación cruciales para el análisis de sentimiento o contexto
descartar = {'no', 'sin', 'ni'}
stop_word = STOP_WORDS - descartar

def quitar_stopwords(col):
    """
    Remueve las palabras vacías (stopwords) de una Serie de pandas.
    
    Convierte el texto a minúsculas, divide las cadenas en palabras, filtra 
    aquellas que pertenecen al conjunto de stopwords configurado y vuelve 
    a reconstruir el texto original sin la carga de conectores innecesarios.
    """
    return (col.fillna('')
            .str.lower()
            .str.split()
            # Unimos las palabras de nuevo con espacios para que sea texto, no una lista
            .apply(lambda x: " ".join([word for word in x if word not in stop_word])))

def limpiar_datos(data_serie):
    """
    Realiza una limpieza integral de texto sobre una Serie de datos.
    
    Aplica de manera secuencial la conversión a minúsculas, la eliminación de 
    signos de puntuación/caracteres especiales mediante expresiones regulares, 
    remueve acentos por sustitución de caracteres y, finalmente, filtra las stopwords.
    """
    acentos = str.maketrans('áéíóúÁÉÍÓÚ', 'aeiouAEIOU')
    # Limpieza de caracteres y acentos
    data = data_serie.astype(str).str.lower()\
        .str.replace(r'[^\w\s]', '', regex=True)\
        .str.translate(acentos)
    # Quitar las stopwords
    data = quitar_stopwords(data)
    return data