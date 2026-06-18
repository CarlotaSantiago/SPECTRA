/**
 * @file types.ts
 * @description Definición centralizada de interfaces y tipos (DTOs) utilizados en todo el frontend.
 * Establece el contrato de datos esperado en la comunicación con el backend de SPECTRA.
 */

/**
 * Interfaz que envuelve un archivo físico y sus metadatos de configuración para la subida.
 */
export interface FileWithSettings {
  /** El objeto File nativo del navegador */
  file: File;
  /** Indica si se debe ejecutar el pipeline de preprocesamiento automático en el backend */
  preprocess: boolean;
}

/**
 * Respuesta del backend tras una subida exitosa (endpoint `/upload`).
 */
export interface UploadResponse {
  status: "ok" | "error";
  /** Ruta o identificador del archivo guardado en el backend */
  path: string;
  /** Número total de filas detectadas en el dataset */
  n_rows: number;
  /** Nombres de las columnas parseadas */
  columnas: string[];
  /** Mensaje de error o éxito adicional */
  message?: string;
}

/**
 * Payload enviado al endpoint `/process-state1`.
 * Define las características del análisis de datos inicial que realizará el sistema.
 */
export interface ManifestPayload {
  n_rows: number;
  path: string;
  features: string[];
  targets: string[];
  shielded: string[];
  /** Modelo LLM pre-seleccionado para la tarea de análisis semántico */
  model: string;
  execution_mode: string;
  /** Configuración para la optimización de hiperparámetros (si aplica en este stage) */
  search_config: {
    search_strategy: string;
    max_iter: number;
    max_combinations: number;
    cv_folds: number;
    timeout_minutes: number;
  };
}

/**
 * Restricciones definidas por el usuario que controlan cómo debe generarse 
 * el código del modelo de Machine Learning final.
 */
export interface UserConstraints {
  /** Estrategia de validación cruzada (ej. StratifiedKFold) y número de folds */
  cv_strategy: { type: string; folds: number };
  /** Umbral para descartar variables poco relevantes */
  feature_selection_threshold: number;
  /** Define si el script generado debe contemplar modelos Ensemble (bagging/boosting) */
  allow_ensembles: boolean;
  /** Prioridades de optimización (ej. ["Performance", "Interpretability"]) */
  optimization_priority: string[];
  /** Preferencias de selección de algoritmos (ej. xgboost, sklearn) */
  model_selection: { mode: string; libraries: string[] };
  /** Estrategia de búsqueda de hiperparámetros (ej. Bayesian_Optimization) */
  tuning_strategy: { search_type: string; max_trials: number; timeout: number };
}

/**
 * Estructura de datos completa (Dossier) devuelta por el backend tras finalizar el State 1.
 * Contiene el análisis semántico de las variables, metadatos y el plan de orquestación lógico.
 */
export interface DossierData {
  categorical_evaluation: Record<string, any>;
  classified_evaluation: Record<string, any>;
  global_metadata: {
    total_rows: number;
    features: number;
    targets: string[];
    sampling_strategy: string;
  };
  /** Define en qué orden y cómo se deben modelar las variables objetivo múltiples (ej. GatedChain) */
  orchestration_plan: {
    strategy: string;
    order: string[];
    gating: string;
    dependents: string[];
    max_dependency: number;
    sub_strategy?: any;
  };
  target_dependency_matrix: Record<string, Record<string, number>>;
  targets_evaluation: Record<string, any>;
  /** Contiene las preferencias inyectadas o definidas por el usuario */
  user_constraints: UserConstraints;
}

/**
 * Payload enviado al endpoint `/process-state2` para generar el script en Python.
 */
export interface GeneratePayload {
  /** El dossier completo resultado del State 1, potencialmente modificado por el usuario */
  dossier: DossierData;
  path: string;
  extension: string;
  /** El modelo LLM responsable de la tarea de generación de código */
  model: string;
  provider?: string;
}
