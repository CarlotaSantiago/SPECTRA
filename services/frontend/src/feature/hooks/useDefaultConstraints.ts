/**
 * @file useDefaultConstraints.ts
 * @description Utilidad para garantizar que un Dossier (estado de análisis)
 * tenga inyectadas las restricciones por defecto antes de ser manipulado.
 */

import type { UserConstraints } from "../../types";


export const DEFAULT_USER_CONSTRAINTS: UserConstraints = {
  cv_strategy: { type: "StratifiedKFold", folds: 10 },
  feature_selection_threshold: 0.05,
  allow_ensembles: true,
  optimization_priority: ["Performance", "Interpretability"],
  model_selection: {
    mode: "AUTONOMOUS_COMPETITION",
    libraries: ["scikit-learn", "xgboost", "lightgbm"],
  },
  tuning_strategy: {
    search_type: "Bayesian_Optimization",
    max_trials: 2,
    timeout: 60,
  },
};

export const initializeDossierConstraints = (base: any): any => {
  if (!base) return null;
  if (base.data && !base.data.user_constraints) {
    base.data.user_constraints = { ...DEFAULT_USER_CONSTRAINTS };
  }
  return base;
};
