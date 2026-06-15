# --- TRAINING SERVICE RUNTIME BOOTSTRAP ---
import os
from pathlib import Path

_DATASET_PATH = Path(os.environ["DATASET_PATH"])
_OUTPUT_PATH = Path(os.environ["OUTPUT_PATH"])
_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

import pandas as pd


def _training_service_redirect_path(filepath_or_buffer, loader):
    if isinstance(filepath_or_buffer, (str, Path)) and not Path(filepath_or_buffer).exists():
        return loader(_DATASET_PATH)
    return loader(filepath_or_buffer)


def _training_service_patch_reader(reader):
    def _patched(filepath_or_buffer, *args, **kwargs):
        return _training_service_redirect_path(
            filepath_or_buffer,
            lambda path: reader(path, *args, **kwargs),
        )

    return _patched


pd.read_csv = _training_service_patch_reader(pd.read_csv)
pd.read_excel = _training_service_patch_reader(pd.read_excel)
pd.read_parquet = _training_service_patch_reader(pd.read_parquet)


def _training_service_load_dataset(path: Path = _DATASET_PATH):
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        return pd.read_excel(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


df = _training_service_load_dataset()
print(
    f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns",
    flush=True,
)
# --- END TRAINING SERVICE RUNTIME BOOTSTRAP ---


import json
import os
import warnings

import joblib
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    f1_score,
    log_loss,
    precision_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

if "resolve_metric" not in globals():

    def _f1_weighted(y_true, y_pred):
        return f1_score(y_true, y_pred, average="weighted", zero_division=0)

    def _precision_weighted(y_true, y_pred):
        return precision_score(y_true, y_pred, average="weighted", zero_division=0)

    def _roc_auc(y_true, y_pred_or_proba):
        try:
            arr = np.asarray(y_pred_or_proba)
            if arr.ndim == 2:
                return roc_auc_score(
                    y_true, y_pred_or_proba, multi_class="ovr", average="weighted"
                )
        except Exception:
            pass
        return roc_auc_score(y_true, y_pred_or_proba, multi_class="ovr", average="weighted")

    METRIC_FUNCTIONS = {
        "f1": _f1_weighted,
        "precision": _precision_weighted,
        "accuracy": accuracy_score,
        "roc_auc": _roc_auc,
        "kappa": cohen_kappa_score,
        "log_loss": log_loss,
    }

    def resolve_metric(scorer):
        return METRIC_FUNCTIONS[scorer]

print("AutoML training script started", flush=True)

_OUTPUT_PATH = os.environ.get("OUTPUT_PATH", _OUTPUT_PATH if "_OUTPUT_PATH" in globals() else "./output")
os.makedirs(_OUTPUT_PATH, exist_ok=True)

if "df" not in globals():
    _DATASET_PATH = os.environ.get("DATASET_PATH", _DATASET_PATH if "_DATASET_PATH" in globals() else None)
    if _DATASET_PATH is None:
        raise RuntimeError("Dataset not pre-loaded and DATASET_PATH is not set")
    df = pd.read_excel(_DATASET_PATH)

print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns", flush=True)

TARGETS = ["sala", "especialidad", "prioridad"]
GATING_TARGET = "sala"
CV_FOLDS = 10
N_TRIALS = 2
OPTUNA_TIMEOUT = 60 
RANDOM_STATE = 42

BASE_FEATURES = ["descrip", "edad", "datosclini", "sospechadiag"]

FEATURE_IG = {
    "sala": {
        "descrip": 0.4967,
        "edad": 0.0442,
        "datosclini": 0.4457,
        "sospechadiag": 0.4808,
    },
    "especialidad": {
        "descrip": 0.4967,
        "edad": 0.0196,
        "datosclini": 0.2348,
        "sospechadiag": 0.2848,
    },
    "prioridad": {
        "descrip": 0.4967,
        "edad": 0.2111,
        "datosclini": 0.3322,
        "sospechadiag": 0.3558,
    },
}

FEATURE_SELECTION_THRESHOLD = 0.05

HYPERPARAMETER_SPACES = {
    "LGBMClassifier": {
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7, -1],
        "n_estimators": [100, 300, 500],
        "num_leaves": [31, 63, 127],
        "subsample": [0.7, 0.85, 1.0],
    },
    "RandomForestClassifier": {
        "max_depth": [None, 5, 10, 20],
        "max_features": ["sqrt", "log2"],
        "min_samples_split": [2, 5, 10],
        "n_estimators": [100, 300, 500],
    },
    "XGBClassifier": {
        "colsample_bytree": [0.7, 0.9, 1.0],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7],
        "n_estimators": [100, 300, 500],
        "subsample": [0.7, 0.9, 1.0],
    },
}

MODEL_CLASSES = {
    "LGBMClassifier": LGBMClassifier,
    "RandomForestClassifier": RandomForestClassifier,
    "XGBClassifier": XGBClassifier,
}

DEFAULT_PARAMS = {
    "LGBMClassifier": {
        "learning_rate": 0.05,
        "max_depth": 5,
        "n_estimators": 300,
        "num_leaves": 63,
        "subsample": 0.85,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbose": -1,
    },
    "RandomForestClassifier": {
        "max_depth": None,
        "max_features": "sqrt",
        "min_samples_split": 2,
        "n_estimators": 300,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
    },
    "XGBClassifier": {
        "colsample_bytree": 0.9,
        "learning_rate": 0.05,
        "max_depth": 5,
        "n_estimators": 300,
        "subsample": 0.9,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": 0,
        "eval_metric": "logloss",
    },
}

TARGETS_EVALUATION = {
    "sala": {"priority_metrics": ["F1-Score"], "optimization_scorer": "f1"},
    "especialidad": {"priority_metrics": ["F1-Score"], "optimization_scorer": "f1"},
    "prioridad": {"priority_metrics": ["F1-Score"], "optimization_scorer": "f1"},
}

METRIC_NAME_TO_SNAKE = {
    "F1-Score": "f1_score",
    "Precision": "precision",
    "Accuracy": "accuracy",
    "AUC-ROC": "roc_auc",
    "Kappa": "kappa",
    "Log-Loss": "log_loss",
}

METRIC_NAME_TO_SCORER = {
    "F1-Score": "f1",
    "Precision": "precision",
    "Accuracy": "accuracy",
    "AUC-ROC": "roc_auc",
    "Kappa": "kappa",
    "Log-Loss": "log_loss",
}

def _str_col_2d(series):
    return series.fillna("").astype(str).to_numpy().reshape(-1, 1)

def _numeric_col_2d(series):
    return pd.to_numeric(series, errors="coerce").fillna(0).to_numpy().reshape(-1, 1)

def _text_array(series):
    return series.fillna("").astype(str).to_numpy()

class FeatureBuilder:
    def __init__(self, feature_names):
        self.feature_names = feature_names
        self.descrip_encoder = None
        self.datosclini_vectorizer = None
        self.sospechadiag_vectorizer = None

    def fit_transform(self, X_df):
        parts = []
        if "descrip" in self.feature_names:
            descrip = _str_col_2d(X_df["descrip"])
            self.descrip_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
            parts.append(self.descrip_encoder.fit_transform(descrip))
        if "edad" in self.feature_names:
            edad = _numeric_col_2d(X_df["edad"])
            parts.append(csr_matrix(edad))
        if "datosclini" in self.feature_names:
            texts = _text_array(X_df["datosclini"])
            self.datosclini_vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=2)
            parts.append(self.datosclini_vectorizer.fit_transform(texts))
        if "sospechadiag" in self.feature_names:
            texts = _text_array(X_df["sospechadiag"])
            self.sospechadiag_vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=2)
            parts.append(self.sospechadiag_vectorizer.fit_transform(texts))
        if not parts:
            raise ValueError("No features selected for matrix construction")
        if len(parts) == 1:
            return parts[0]
        return hstack(parts).tocsr()

    def transform(self, X_df):
        parts = []
        if "descrip" in self.feature_names:
            descrip = _str_col_2d(X_df["descrip"])
            parts.append(self.descrip_encoder.transform(descrip))
        if "edad" in self.feature_names:
            edad = _numeric_col_2d(X_df["edad"])
            parts.append(csr_matrix(edad))
        if "datosclini" in self.feature_names:
            texts = _text_array(X_df["datosclini"])
            parts.append(self.datosclini_vectorizer.transform(texts))
        if "sospechadiag" in self.feature_names:
            texts = _text_array(X_df["sospechadiag"])
            parts.append(self.sospechadiag_vectorizer.transform(texts))
        if len(parts) == 1:
            return parts[0]
        return hstack(parts).tocsr()

def to_json_serializable(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): to_json_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_serializable(v) for v in value]
    return value

def selected_features_for_target(target):
    scores = FEATURE_IG[target]
    return [feat for feat in BASE_FEATURES if scores.get(feat, 0.0) >= FEATURE_SELECTION_THRESHOLD]

def append_chain_features(X_matrix, chain_encoded_columns):
    if not chain_encoded_columns:
        return X_matrix
    chain_matrix = csr_matrix(np.column_stack(chain_encoded_columns))
    return hstack([X_matrix, chain_matrix]).tocsr()

def suggest_hyperparameters(trial, model_name):
    space = HYPERPARAMETER_SPACES[model_name]
    params = {}
    for key, choices in space.items():
        param_name = f"{model_name}__{key}"
        params[key] = trial.suggest_categorical(param_name, choices)
    params["random_state"] = RANDOM_STATE
    params["n_jobs"] = -1
    if model_name == "LGBMClassifier":
        params["verbose"] = -1
    if model_name == "XGBClassifier":
        params["verbosity"] = 0
        params["eval_metric"] = "logloss"
    return params

def create_model(model_name, params):
    return MODEL_CLASSES[model_name](**params)

def compute_metric(scorer_key, y_true, y_pred, y_proba=None):
    metric_fn = resolve_metric(scorer_key)
    if scorer_key in ("roc_auc", "log_loss") and y_proba is not None:
        try:
            return float(metric_fn(y_true, y_proba))
        except Exception:
            return float(metric_fn(y_true, y_pred))
    return float(metric_fn(y_true, y_pred))

def compute_priority_metrics(target, y_true, y_pred, y_proba=None):
    metrics = {}
    for metric_name in TARGETS_EVALUATION[target]["priority_metrics"]:
        scorer_key = METRIC_NAME_TO_SCORER[metric_name]
        snake_name = METRIC_NAME_TO_SNAKE[metric_name]
        try:
            metrics[snake_name] = compute_metric(scorer_key, y_true, y_pred, y_proba)
        except Exception as exc:
            print(f"Warning: could not compute {metric_name} for {target}: {exc}", flush=True)
            metrics[snake_name] = None
    return metrics

def fit_predict_fold(model, X_train, y_train, X_val):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    y_proba = None
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(X_val)
        except Exception:
            y_proba = None
    return y_pred, y_proba

def build_chain_predictions(chain_specs, X_train_frame, X_val_frame, y_dict):
    chain_train_cols = []
    chain_val_cols = []
    for chain_target, chain_model_name, chain_params, chain_le, chain_features in chain_specs:
        builder = FeatureBuilder(chain_features)
        chain_train_matrix = builder.fit_transform(X_train_frame)
        chain_val_matrix = builder.transform(X_val_frame)
        chain_y = y_dict[chain_target].loc[X_train_frame.index].values
        chain_model = create_model(chain_model_name, chain_params.copy())
        chain_model.fit(chain_train_matrix, chain_y)
        chain_train_pred = chain_model.predict(chain_train_matrix)
        chain_val_pred = chain_model.predict(chain_val_matrix)
        chain_train_cols.append(chain_train_pred.reshape(-1, 1))
        chain_val_cols.append(chain_val_pred.reshape(-1, 1))
    return chain_train_cols, chain_val_cols

def make_objective(
    target,
    X_frame,
    y_series,
    y_dict,
    feature_names,
    chain_specs,
    optimization_scorer,
    n_splits,
):
    def objective(trial):
        model_name = trial.suggest_categorical(
            "model_name", ["LGBMClassifier", "RandomForestClassifier", "XGBClassifier"]
        )
        params = suggest_hyperparameters(trial, model_name)
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        fold_scores = []

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_frame, y_series.values)):
            X_train_frame = X_frame.iloc[train_idx]
            X_val_frame = X_frame.iloc[val_idx]
            y_train = y_series.iloc[train_idx]
            y_val = y_series.iloc[val_idx]

            builder = FeatureBuilder(feature_names)
            X_train_base = builder.fit_transform(X_train_frame)
            X_val_base = builder.transform(X_val_frame)

            chain_train_cols, chain_val_cols = build_chain_predictions(
                chain_specs, X_train_frame, X_val_frame, y_dict
            )

            X_train = append_chain_features(X_train_base, chain_train_cols)
            X_val = append_chain_features(X_val_base, chain_val_cols)

            model = create_model(model_name, params.copy())
            y_pred, _ = fit_predict_fold(model, X_train, y_train.values, X_val)
            score = compute_metric(optimization_scorer, y_val.values, y_pred)
            fold_scores.append(score)
            trial.report(float(np.mean(fold_scores)), fold_idx)
            if trial.should_prune():
                raise optuna.TrialPruned()

        mean_score = float(np.mean(fold_scores))
        print(
            f"Target={target} trial={trial.number} model={model_name} cv_score={mean_score:.6f}",
            flush=True,
        )
        return mean_score

    return objective

def run_optuna_study(target, objective):
    print(f"Starting Optuna optimization for target={target} with {N_TRIALS} trials", flush=True)
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=N_TRIALS, timeout=OPTUNA_TIMEOUT, catch=(Exception,))
    has_complete = any(t.state.name == "COMPLETE" for t in study.trials)
    if has_complete:
        best_params = dict(study.best_params)
        best_value = float(study.best_value)
        model_name = best_params.pop("model_name")
        prefixed_keys = [k for k in list(best_params.keys()) if k.startswith(f"{model_name}__")]
        for pk in prefixed_keys:
            best_params[pk.replace(f"{model_name}__", "", 1)] = best_params.pop(pk)
        print(
            f"Optuna complete for target={target}: best_model={model_name} best_cv_score={best_value:.6f}",
            flush=True,
        )
        return model_name, best_params, best_value
    print(
        f"Warning: no completed Optuna trials for target={target}; using default hyperparameters",
        flush=True,
    )
    return "LGBMClassifier", DEFAULT_PARAMS["LGBMClassifier"].copy(), None

def save_aggregated_metrics(all_target_metrics):
    aggregated_path = os.path.join(_OUTPUT_PATH, "metrics.json")
    payload = {"targets": {entry["target"]: entry for entry in all_target_metrics}}
    with open(aggregated_path, "w", encoding="utf-8") as f:
        json.dump(to_json_serializable(payload), f, indent=2)
    print(f"Aggregated metrics saved to {aggregated_path}", flush=True)

def train_target(
    target,
    X_full,
    y_full,
    y_dict,
    feature_names,
    chain_specs,
    all_target_metrics,
):
    print(f"Training phase started for target={target}", flush=True)
    optimization_scorer = TARGETS_EVALUATION[target]["optimization_scorer"]

    objective = make_objective(
        target=target,
        X_frame=X_full,
        y_series=y_full,
        y_dict=y_dict,
        feature_names=feature_names,
        chain_specs=chain_specs,
        optimization_scorer=optimization_scorer,
        n_splits=CV_FOLDS,
    )

    model_name, best_params, cv_score = run_optuna_study(target, objective)

    if cv_score is None:
        cv_score = 0.0

    builder = FeatureBuilder(feature_names)
    X_base = builder.fit_transform(X_full)

    chain_encoded_columns = []
    chain_artifacts = []
    for chain_target, chain_model_name, chain_params, chain_le, chain_features in chain_specs:
        chain_builder = FeatureBuilder(chain_features)
        chain_matrix = chain_builder.fit_transform(X_full)
        chain_y = y_dict[chain_target].values
        chain_model = create_model(chain_model_name, chain_params.copy())
        chain_model.fit(chain_matrix, chain_y)
        chain_pred = chain_model.predict(chain_matrix)
        chain_encoded_columns.append(chain_pred.reshape(-1, 1))
        chain_artifacts.append(
            {
                "target": chain_target,
                "model_name": chain_model_name,
                "params": chain_params,
                "label_encoder": chain_le,
                "features": chain_features,
                "model": chain_model,
                "feature_builder": chain_builder,
            }
        )

    X_final = append_chain_features(X_base, chain_encoded_columns)
    final_model = create_model(model_name, best_params.copy())
    final_model.fit(X_final, y_full.values)

    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    oof_pred = pd.Series(index=y_full.index, dtype=float)
    oof_proba = None
    for train_idx, val_idx in skf.split(X_final, y_full.values):
        fold_builder = FeatureBuilder(feature_names)
        X_train_base = fold_builder.fit_transform(X_full.iloc[train_idx])
        X_val_base = fold_builder.transform(X_full.iloc[val_idx])
        chain_train_cols, chain_val_cols = build_chain_predictions(
            chain_specs, X_full.iloc[train_idx], X_full.iloc[val_idx], y_dict
        )
        X_train = append_chain_features(X_train_base, chain_train_cols)
        X_val = append_chain_features(X_val_base, chain_val_cols)
        fold_model = create_model(model_name, best_params.copy())
        y_pred, y_proba = fit_predict_fold(
            fold_model, X_train, y_full.iloc[train_idx].values, X_val
        )
        oof_pred.iloc[val_idx] = y_pred
        if y_proba is not None:
            if oof_proba is None:
                oof_proba = np.zeros((len(y_full), y_proba.shape[1]))
            oof_proba[val_idx] = y_proba

    metrics = compute_priority_metrics(
        target, y_full.values, oof_pred.values.astype(int), oof_proba
    )

    model_file = f"{target}_model.joblib"
    model_path = os.path.join(_OUTPUT_PATH, model_file)
    artifact = {
        "target": target,
        "model_name": model_name,
        "model": final_model,
        "best_params": best_params,
        "feature_names": feature_names,
        "feature_builder": builder,
        "chain_artifacts": chain_artifacts,
        "label_encoder": label_encoders[target],
    }
    joblib.dump(artifact, model_path)
    print(f"Model persisted for target={target} at {model_path}", flush=True)

    target_metrics = {
        "target": target,
        "model_file": model_file,
        "best_params": to_json_serializable({"model_name": model_name, **best_params}),
        "optimization_metric": optimization_scorer,
        "cv_score": float(cv_score),
        "priority_metrics": TARGETS_EVALUATION[target]["priority_metrics"],
        "metrics": to_json_serializable(metrics),
    }

    target_metrics_path = os.path.join(_OUTPUT_PATH, f"{target}_metrics.json")
    with open(target_metrics_path, "w", encoding="utf-8") as f:
        json.dump(to_json_serializable(target_metrics), f, indent=2)
    print(f"Metrics persisted for target={target} at {target_metrics_path}", flush=True)

    all_target_metrics.append(target_metrics)
    save_aggregated_metrics(all_target_metrics)

    return model_name, best_params, final_model

print("Preparing targets and label encoders", flush=True)

X_all = df[BASE_FEATURES].copy()
label_encoders = {}
y_encoded = {}

for target in TARGETS:
    y_raw = df[target]
    valid = y_raw.notna()
    le = LabelEncoder()
    y_fit = y_raw.loc[valid].astype(str)
    y_encoded[target] = pd.Series(le.fit_transform(y_fit.to_numpy()), index=y_fit.index)
    label_encoders[target] = le
    assert y_encoded[target].notna().all()

valid_rows = df[TARGETS].notna().all(axis=1)
X_work = X_all.loc[valid_rows].copy()
for target in TARGETS:
    y_encoded[target] = y_encoded[target].loc[valid_rows]
    assert y_encoded[target].notna().all()

print(f"Working set after target filtering: {X_work.shape[0]} rows", flush=True)

all_target_metrics = []
trained_models = {}

sala_features = selected_features_for_target("sala")
print(f"GatedChain phase: training gating target={GATING_TARGET}", flush=True)
sala_model_name, sala_params, sala_model = train_target(
    target="sala",
    X_full=X_work,
    y_full=y_encoded["sala"],
    y_dict=y_encoded,
    feature_names=sala_features,
    chain_specs=[],
    all_target_metrics=all_target_metrics,
)
trained_models["sala"] = (sala_model_name, sala_params)

especialidad_features = selected_features_for_target("especialidad")
print("GatedChain phase: training target=especialidad with sala chain dependency", flush=True)
esp_chain = [
    (
        "sala",
        trained_models["sala"][0],
        trained_models["sala"][1],
        label_encoders["sala"],
        sala_features,
    )
]
esp_model_name, esp_params, esp_model = train_target(
    target="especialidad",
    X_full=X_work,
    y_full=y_encoded["especialidad"],
    y_dict=y_encoded,
    feature_names=especialidad_features,
    chain_specs=esp_chain,
    all_target_metrics=all_target_metrics,
)
trained_models["especialidad"] = (esp_model_name, esp_params)

prioridad_features = selected_features_for_target("prioridad")
print("GatedChain phase: training dependent target=prioridad", flush=True)
prior_chain = [
    (
        "sala",
        trained_models["sala"][0],
        trained_models["sala"][1],
        label_encoders["sala"],
        sala_features,
    ),
    (
        "especialidad",
        trained_models["especialidad"][0],
        trained_models["especialidad"][1],
        label_encoders["especialidad"],
        especialidad_features,
    ),
]
prior_model_name, prior_params, prior_model = train_target(
    target="prioridad",
    X_full=X_work,
    y_full=y_encoded["prioridad"],
    y_dict=y_encoded,
    feature_names=prioridad_features,
    chain_specs=prior_chain,
    all_target_metrics=all_target_metrics,
)
trained_models["prioridad"] = (prior_model_name, prior_params)

print("AutoML training script completed successfully", flush=True)