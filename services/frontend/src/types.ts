// src/types.ts
export interface FileWithSettings {
  file: File;
  preprocess: boolean;
}

export interface ManifestPayload{
    n_rows: number;
    path: string;
    features: string[];
    targets: string[];
    shielded: string[];
    model: string;
    execution_mode: string;
    search_config: {
      search_strategy: string;
      max_iter: number;
      max_combinations: number;
      cv_folds: number;
      timeout_minutes: number;
    }
}

export interface DossierData {
  categorical_evaluation: Record<string, any>;
  classified_evaluation: Record<string, any>;
  global_metadata: {
    total_rows: number;
    features: number;
    targets: string[];
    sampling_strategy: string;
  };
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
  user_constraints: Record<string, any>;
}

export interface GeneratePayload{
  dossier: DossierData;
  path: string;
  extension: string;
  model: string;
  provider?: string;
}
