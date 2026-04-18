// src/types.ts
export interface FileWithSettings {
  file: File;
  preprocess: boolean;
}

export interface DossierPayload{
    n_rows: number;
    path: string;
    features: string[];
    targets: string[];
    mandatory: string[];
}