from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- REQUEST SCHEMAS ---

class SearchConfigSchema(BaseModel):
    search_strategy: str = Field(..., max_length=50, description="Estrategia de búsqueda a utilizar")
    max_iter: int = Field(..., gt=0, le=5000, description="Número máximo de iteraciones")
    max_combinations: int = Field(..., gt=0, le=10000, description="Combinaciones máximas a probar")
    cv_folds: int = Field(..., gt=1, le=20, description="Número de folds para Cross Validation")
    timeout_minutes: int = Field(..., gt=0, le=1440, description="Tiempo de espera en minutos")

class ManifestSchema(BaseModel):
    n_rows: int = Field(..., gt=0, description="Número de filas del dataset")
    path: str = Field(..., max_length=1024, description="Ruta absoluta o relativa del dataset")
    features: List[str] = Field(..., max_items=5000, description="Lista de características seleccionadas")
    targets: List[str] = Field(..., min_items=1, max_items=100, description="Variables objetivo")
    shielded: List[str] = Field(..., description="Características protegidas/obligatorias")
    model: str = Field(..., max_length=100, description="Nombre del modelo LLM a utilizar")
    execution_mode: str = Field(..., max_length=50)
    search_config: SearchConfigSchema

class ScriptExecutionPayload(BaseModel):
    script: str = Field(..., min_length=1, description="Código fuente a ejecutar")
    path: Optional[str] = Field(None, max_length=1024, description="Ruta asociada a la ejecución")
    output_path: Optional[str] = Field(None, max_length=1024)
    manifest: Optional[Dict[str, Any]] = None
    # Parámetros de entrenamiento seleccionables por el usuario
    max_trials: Optional[int] = Field(None, gt=0, le=1000, description="Número máximo de trials de Optuna")
    cv_folds: Optional[int] = Field(None, gt=1, le=20, description="Número de folds para validación cruzada")
    timeout_minutes: Optional[int] = Field(None, gt=0, le=1440, description="Tiempo máximo de optimización en minutos")

# --- RESPONSE SCHEMAS ---

class GenericResponse(BaseModel):
    status: str
    message: Optional[str] = None

class UploadResponse(BaseModel):
    status: str
    n_rows: int
    columnas: List[str]
    preview: List[Dict[str, Any]]
    path: str

class PageResponse(BaseModel):
    status: str
    items: List[Dict[str, Any]]
    n_rows: int
    page: int
    size: int

class ModelsResponse(BaseModel):
    status: str
    models: List[str]
