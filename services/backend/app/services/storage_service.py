import io
import os
import re
import pandas as pd
from typing import Union
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Rutas base para almacenamiento
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
MODEL_DIR = BASE_DIR / "model"

# Asegurar que existan al inicio
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def secure_filename(filename: str) -> str:
    """
    Sanitiza el nombre del archivo para prevenir Path Traversal y caracteres peligrosos.
    Permite letras, números, puntos, guiones y guiones bajos.
    """
    if not filename:
        return "unnamed_file"
    filename = os.path.basename(filename) # Quita directorios
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename

class StorageService:
    @staticmethod
    def read_dataset(target: Union[str, UploadFile]) -> pd.DataFrame:
        """
        Lee un dataset de forma dinámica. 
        Soporta strings (rutas en disco) u objetos UploadFile de FastAPI.
        """
        if isinstance(target, str):
            # Seguridad: Verificar que la ruta resuelta está dentro del directorio permitido
            try:
                target_path = Path(target).resolve()
                if not (target_path.is_relative_to(UPLOADS_DIR) or target_path.is_relative_to(MODEL_DIR) or target_path.is_relative_to(BASE_DIR)):
                    raise HTTPException(status_code=403, detail="Acceso denegado a la ruta especificada.")
            except AttributeError:
                pass # Fallback

            filename = target
            source = target
        elif hasattr(target, 'filename'):  # UploadFile
            filename = target.filename
            target.file.seek(0)
            source = io.BytesIO(target.file.read())
        else:
            raise ValueError("El formato del objeto provisto no es mapeable a un dataset")
        
        if filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(source)
        elif filename.endswith('.csv'):
            return pd.read_csv(source)
        elif filename.endswith('.parquet'):
            return pd.read_parquet(source)
        else:
            raise ValueError(f"Formato de archivo no soportado: {filename}")

    @staticmethod
    def save_dataset(data: pd.DataFrame, path: Union[str, Path]) -> str:
        """
        Guarda un DataFrame en disco y devuelve la ruta absoluta guardada.
        Aplica sanitización al nombre del archivo para seguridad.
        """
        path_obj = Path(path)
        safe_name = secure_filename(path_obj.name)
        safe_dir = path_obj.parent
        
        # Aseguramos que se guarde en UPLOADS_DIR si no se especifica directorio o es relativo
        if str(safe_dir) == '.' or not safe_dir.is_absolute():
             safe_path_str = str(UPLOADS_DIR / safe_name)
        else:
             safe_path_str = str(safe_dir / safe_name)
             
        if safe_path_str.endswith(('.xlsx', '.xls')):
            data.to_excel(safe_path_str, index=False)
        elif safe_path_str.endswith('.csv'):
            data.to_csv(safe_path_str, index=False)
        elif safe_path_str.endswith('.parquet'):
            data.to_parquet(safe_path_str, index=False)
        else:
            raise ValueError("Formato de archivo no soportado para guardado")
        return safe_path_str
