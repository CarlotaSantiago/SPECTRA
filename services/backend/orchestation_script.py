import subprocess; subprocess.run(["pip", "install", "lightgbm"], check=True)

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from optuna import create_study, TrialPruned, pruners

def build_preprocessor(feature_profiles):
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), [col for col, prof in feature_profiles.items() if prof['subclass'] == 'numeric']),
            ('cat', OrdinalEncoder(handle_unknown='ignore'), [col for col, prof in feature_profiles.items() if prof['subclass'] in ['NOMINAL', 'ORDINAL']])
        ]
    )
    return preprocessor

def build_gating_model(X_train, y_train, preprocessor, cv, timeout_minutes):
    study = create_study(direction='maximize', pruner=pruners.TimePruning(timeout_minutes * 60))

    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
            'learning_rate': trial.suggest_loguniform('learning_rate', 1e-3, 1e-1),
            'max_depth': trial.suggest_int('max_depth', 3, 12),
            'num_leaves': trial.suggest_int('num_leaves', 20, 256),
            'colsample_bytree': trial.suggest_uniform('colsample_bytree', 0.5, 1.0),
            'subsample': trial.suggest_uniform('subsample', 0.5, 1.0)
        }

        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', LGBMClassifier(**params))
        ])

        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='accuracy')
        mean_cv_score = cv_scores.mean()

        if trial.should_prune():
            raise TrialPruned()

        return mean_cv_score

    study.optimize(objective, n_trials=100)

    best_params = study.best_params
    fitted_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', LGBMClassifier(**best_params))
    ]).fit(X_train, y_train)

    cv_score = cross_val_score(fitted_pipeline, X_train, y_train, cv=cv, scoring='accuracy').mean()

    return fitted_pipeline, best_params, cv_score