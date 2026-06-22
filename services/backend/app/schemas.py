"""
Módulo de esquemas Pydantic.

Este módulo define las estructuras de datos requeridas para la validación
de entrada (Request) y la serialización de salida (Response) en la API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- REQUEST SCHEMAS ---

class SearchConfigSchema(BaseModel):
    """
    Esquema que define la configuración de la búsqueda de hiperparámetros
    y estrategias de validación.
    """
    search_strategy: str = Field(..., max_length=50, description="Estrategia de búsqueda a utilizar")
    max_iter: int = Field(..., gt=0, le=5000, description="Número máximo de iteraciones")
    max_combinations: int = Field(..., gt=0, le=10000, description="Combinaciones máximas a probar")
    cv_folds: int = Field(..., gt=1, le=20, description="Número de folds para Cross Validation")
    timeout_minutes: int = Field(..., gt=0, le=1440, description="Tiempo de espera en minutos")

class ManifestSchema(BaseModel):
    """
    Esquema principal del manifiesto.
    Contiene la metadata del dataset y las variables seleccionadas.
    """
    n_rows: int = Field(..., gt=0, description="Número de filas del dataset")
    path: str = Field(..., max_length=1024, description="Ruta absoluta o relativa del dataset")
    features: List[str] = Field(
        ..., max_items=5000, description="Lista de características seleccionadas"
    )
    targets: List[str] = Field(..., min_items=1, max_items=100, description="Variables objetivo")
    shielded: List[str] = Field(..., description="Características protegidas/obligatorias")
    model: str = Field(..., max_length=100, description="Nombre del modelo LLM a utilizar")
    execution_mode: str = Field(..., max_length=50)
    search_config: SearchConfigSchema

class ScriptExecutionPayload(BaseModel):
    """
    Esquema para la carga útil que solicita la ejecución de un script de Python,
    usualmente procesado por el entorno aislado (Sandbox).
    """
    script: str = Field(..., min_length=1, description="Código fuente a ejecutar")
    path: Optional[str] = Field(None, max_length=1024, description="Ruta asociada a la ejecución")
    output_path: Optional[str] = Field(None, max_length=1024)
    manifest: Optional[Dict[str, Any]] = None
    # Parámetros de entrenamiento seleccionables por el usuario
    max_trials: Optional[int] = Field(
        None, gt=0, le=1000, description="Número máximo de trials de Optuna"
    )
    cv_folds: Optional[int] = Field(
        None, gt=1, le=20, description="Número de folds para validación cruzada"
    )
    timeout_minutes: Optional[int] = Field(
        None, gt=0, le=1440, description="Tiempo máximo de optimización en min"
    )

# --- RESPONSE SCHEMAS ---

class GenericResponse(BaseModel):
    """Esquema para una respuesta genérica estándar."""
    status: str
    message: Optional[str] = None

class UploadResponse(BaseModel):
    """Esquema de respuesta tras la subida exitosa de un archivo."""
    status: str
    n_rows: int
    columnas: List[str]
    preview: List[Dict[str, Any]]
    path: str

class PageResponse(BaseModel):
    """Esquema de respuesta para la paginación de datos."""
    status: str
    items: List[Dict[str, Any]]
    n_rows: int
    page: int
    size: int

class ModelsResponse(BaseModel):
    """Esquema de respuesta que devuelve la lista de modelos de IA disponibles."""
    status: str
    models: List[str]
