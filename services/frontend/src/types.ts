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