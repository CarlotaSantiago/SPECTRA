import pandas as pd
from spacy.lang.es.stop_words import STOP_WORDS
import io
import os

# 1. Configuración de Stopwords
descartar = {'no', 'sin', 'ni'}
stop_word = STOP_WORDS - descartar

def quitar_stopwords(col):
    """Remove stopwords from a pandas Series of text."""
    return (col.fillna('')
            .str.lower()
            .str.split()
            # Unimos las palabras de nuevo con espacios para que sea texto, no una lista
            .apply(lambda x: " ".join([word for word in x if word not in stop_word])))

def limpiar_datos(data_serie):
    """Clean text data by removing special characters, accents, and stopwords."""
    acentos = str.maketrans('áéíóúÁÉÍÓÚ', 'aeiouAEIOU')
    # Limpieza de caracteres y acentos
    data = data_serie.astype(str).str.lower()\
        .str.replace(r'[^\w\s]', '', regex=True)\
        .str.translate(acentos)
    # Quitar las stopwords
    data = quitar_stopwords(data)
    return data
