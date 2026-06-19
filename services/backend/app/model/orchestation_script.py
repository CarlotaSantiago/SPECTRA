import json
import os
import warnings
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

try:
    _OUTPUT_PATH
except NameError:
    _OUTPUT_PATH = os.environ.get("OUTPUT_PATH", ".")

try:
    df
except NameError:
    _DATASET_PATH = os.environ.get("DATASET_PATH", "/app/uploads/datos_limpios.xlsx")
    df = pd.read_excel(_DATASET_PATH)

try:
    resolve_metric
except NameError:
    from sklearn.metrics import accuracy_score, f1_score, precision_score, roc_auc_score

    def resolve_metric(scorer: str):
        mapping = {
            "f1": lambda y_true, y_pred, **kw: f1_score(
                y_true, y_pred, average="weighted", zero_division=0, **kw
            ),
            "f1_score": lambda y_true, y_pred, **kw: f1_score(
                y_true, y_pred, average="weighted", zero_division=0, **kw
            ),
            "precision": lambda y_true, y_pred, **kw: precision_score(
                y_true, y_pred, average="weighted", zero_division=0, **kw
            ),
            "accuracy": lambda y_true, y_pred, **kw: accuracy_score(y_true, y_pred, **kw),
            "roc_auc": lambda y_true, y_pred, **kw: roc_auc_score(
                y_true, y_pred, multi_class="ovr", average="weighted", **kw
            ),
        }
        return mapping[scorer]

BASE_FEATURES = ["descrip", "edad", "datosclini", "sospechadiag"]
TARGETS = ["especialidad", "sala", "prioridad"]
CV_FOLDS = 10
MAX_TRIALS = 50
OPTUNA_TIMEOUT = 60
OPTIMIZATION_SCORER = "f1"

PRIORITY_METRIC_DISPLAY = {
    "especialidad": ["F1-Score"],
    "sala": ["F1-Score"],
    "prioridad": ["F1-Score"],
}

METRIC_NAME_TO_SCORER = {
    "F1-Score": "f1",
    "Precision": "precision",
    "Accuracy": "accuracy",
    "AUC-ROC": "roc_auc",
}

METRIC_NAME_TO_JSON_KEY = {
    "F1-Score": "f1_score",
    "Precision": "precision",
    "Accuracy": "accuracy",
    "AUC-ROC": "auc_roc",
    "Kappa": "kappa",
    "Log-Loss": "log_loss",
}

BASE_HYPERPARAMETER_SPACES = {
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

DEFAULT_PARAMS = {
    "LGBMClassifier": {
        "learning_rate": 0.05,
        "max_depth": 5,
        "n_estimators": 100,
        "num_leaves": 31,
        "subsample": 0.85,
    },
    "RandomForestClassifier": {
        "max_depth": 10,
        "max_features": "sqrt",
        "min_samples_split": 2,
        "n_estimators": 100,
    },
    "XGBClassifier": {
        "colsample_bytree": 0.9,
        "learning_rate": 0.05,
        "max_depth": 5,
        "n_estimators": 100,
        "subsample": 0.9,
    },
}

def to_json_serializable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value

def normalize_predictions(y_pred: np.ndarray) -> np.ndarray:
    arr = np.asarray(y_pred)
    if arr.ndim > 1:
        if arr.shape[1] > 1:
            arr = np.argmax(arr, axis=1)
        else:
            arr = arr.ravel()
    return arr.astype(int)

def suggest_hyperparameters(trial: optuna.Trial, model_name: str) -> Dict[str, Any]:
    space = BASE_HYPERPARAMETER_SPACES[model_name]
    params: Dict[str, Any] = {}
    for key, values in space.items():
        params[key] = trial.suggest_categorical(key, values)
    return params

def build_classifier(model_name: str, params: Dict[str, Any], num_classes: int):
    if num_classes < 2:
        raise ValueError(f"Classification requires at least 2 classes, got {num_classes}")

    if model_name == "LGBMClassifier":
        lgbm_kwargs = dict(
            random_state=42,
            n_jobs=-1,
            verbose=-1,
            force_col_wise=True,
            **params,
        )
        if num_classes == 2:
            return LGBMClassifier(objective="binary", **lgbm_kwargs)
        return LGBMClassifier(objective="multiclass", num_class=num_classes, **lgbm_kwargs)

    if model_name == "RandomForestClassifier":
        return RandomForestClassifier(random_state=42, n_jobs=-1, **params)

    if model_name == "XGBClassifier":
        xgb_kwargs = dict(
            random_state=42,
            n_jobs=-1,
            verbosity=0,
            **params,
        )
        if num_classes == 2:
            return XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                **xgb_kwargs,
            )
        return XGBClassifier(
            objective="multi:softprob",
            num_class=num_classes,
            eval_metric="mlogloss",
            **xgb_kwargs,
        )

    raise ValueError(f"Unsupported model: {model_name}")

class FeatureEncoder:
    def __init__(self, columns: List[str]):
        self.columns = columns
        self.encoders: Dict[str, LabelEncoder] = {}

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        encoded_parts = []
        for col in self.columns:
            le = LabelEncoder()
            values = X[col].astype(str).fillna("__MISSING__")
            encoded = le.fit_transform(values)
            self.encoders[col] = le
            encoded_parts.append(encoded.reshape(-1, 1))
        return np.hstack(encoded_parts)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        encoded_parts = []
        for col in self.columns:
            le = self.encoders[col]
            values = X[col].astype(str).fillna("__MISSING__")
            known = set(le.classes_)
            fallback = "__MISSING__" if "__MISSING__" in known else le.classes_[0]
            safe_values = values.apply(lambda v: v if v in known else fallback)
            encoded = le.transform(safe_values)
            encoded_parts.append(encoded.reshape(-1, 1))
        return np.hstack(encoded_parts)

def prepare_base_frame(raw_df: pd.DataFrame) -> pd.DataFrame:
    frame = raw_df.copy()
    frame["edad"] = pd.to_numeric(frame["edad"], errors="coerce")
    frame["edad"] = frame["edad"].fillna(frame["edad"].median())
    for col in ["descrip", "datosclini", "sospechadiag"]:
        frame[col] = frame[col].astype(str).fillna("__MISSING__")
    return frame

def encode_target(y_raw: pd.Series) -> Tuple[pd.Series, LabelEncoder]:
    valid = y_raw.notna()
    le = LabelEncoder()
    encoded = pd.Series(index=y_raw.index, dtype="float64")
    encoded.loc[valid] = le.fit_transform(y_raw.loc[valid].astype(str))
    return encoded, le

def prepare_xy(
    frame: pd.DataFrame,
    target: str,
    extra_feature_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    feature_cols = list(BASE_FEATURES)
    if extra_feature_cols:
        feature_cols.extend(extra_feature_cols)
    y_raw = frame[target]
    valid = y_raw.notna()
    X = frame.loc[valid, BASE_FEATURES].copy()
    if extra_feature_cols:
        for col in extra_feature_cols:
            X[col] = np.nan
    y, target_encoder = encode_target(y_raw.loc[valid])
    assert y.notna().all(), f"Target {target} contains missing values after filtering"
    return X, y.astype(int), target_encoder

def score_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray],
    scorer: str,
) -> float:
    y_true_arr = np.asarray(y_true).ravel()
    y_pred_arr = normalize_predictions(y_pred)
    metric_fn = resolve_metric(scorer)
    if scorer == "roc_auc" and y_proba is not None:
        from sklearn.metrics import roc_auc_score

        proba = np.asarray(y_proba)
        if proba.ndim == 1:
            return float(roc_auc_score(y_true_arr, proba))
        n_classes = proba.shape[1]
        if n_classes == 2:
            return float(roc_auc_score(y_true_arr, proba[:, 1]))
        return float(
            roc_auc_score(y_true_arr, proba, multi_class="ovr", average="weighted")
        )
    return float(metric_fn(y_true_arr, y_pred_arr))

def cross_validate_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    params: Dict[str, Any],
    scorer: str,
    parent_predictions: Optional[pd.DataFrame] = None,
) -> float:
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=42)
    scores: List[float] = []
    num_classes = int(y.nunique())
    if num_classes < 2:
        return 0.0

    for train_idx, val_idx in skf.split(X, y):
        X_train = X.iloc[train_idx].copy()
        X_val = X.iloc[val_idx].copy()
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]

        if int(y_train.nunique()) < 2:
            continue

        feature_cols = list(BASE_FEATURES)
        extra_cols: List[str] = []
        if parent_predictions is not None:
            extra_cols = [c for c in parent_predictions.columns if c not in BASE_FEATURES]
            feature_cols.extend(extra_cols)
            for col in extra_cols:
                X_train[col] = parent_predictions.iloc[train_idx][col].values
                X_val[col] = parent_predictions.iloc[val_idx][col].values

        encoder = FeatureEncoder(feature_cols)
        X_train_enc = encoder.fit_transform(X_train)
        X_val_enc = encoder.transform(X_val)

        model = build_classifier(model_name, params, num_classes)
        model.fit(X_train_enc, y_train.values)
        y_pred = normalize_predictions(model.predict(X_val_enc))
        y_proba = model.predict_proba(X_val_enc) if hasattr(model, "predict_proba") else None
        fold_score = score_predictions(y_val.values, y_pred, y_proba, scorer)
        scores.append(fold_score)

    if not scores:
        return 0.0
    return float(np.mean(scores))

def build_parent_predictions_for_cv(
    frame: pd.DataFrame,
    parent_targets: List[str],
    parent_model_names: List[str],
    parent_params: List[Dict[str, Any]],
    parent_encoders: List[LabelEncoder],
) -> pd.DataFrame:
    parent_df = pd.DataFrame(index=frame.index)
    prior_oof_cols: List[str] = []

    for parent_target, model_name, params, target_le in zip(
        parent_targets, parent_model_names, parent_params, parent_encoders
    ):
        y_raw = frame[parent_target]
        valid = y_raw.notna()
        X_base = frame.loc[valid, BASE_FEATURES].copy()
        encoded_values = target_le.transform(y_raw.loc[valid].astype(str))
        y = pd.Series(encoded_values, index=X_base.index, dtype=int)
        for col in prior_oof_cols:
            X_base[col] = parent_df.loc[X_base.index, col].values

        oof = pd.Series(index=frame.index, dtype="float64")
        num_classes = len(target_le.classes_)
        if num_classes < 2:
            pred_col = f"{parent_target}_pred"
            parent_df[pred_col] = oof
            prior_oof_cols.append(pred_col)
            continue

        feature_cols = list(BASE_FEATURES) + prior_oof_cols
        skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=42)

        for train_idx, val_idx in skf.split(X_base, y):
            train_index = X_base.index[train_idx]
            val_index = X_base.index[val_idx]
            X_train = X_base.loc[train_index, feature_cols].copy()
            X_val = X_base.loc[val_index, feature_cols].copy()
            y_train = y.loc[train_index]

            if int(y_train.nunique()) < 2:
                continue

            encoder = FeatureEncoder(feature_cols)
            X_train_enc = encoder.fit_transform(X_train)
            X_val_enc = encoder.transform(X_val)

            model = build_classifier(model_name, params, num_classes)
            model.fit(X_train_enc, y_train.values)
            preds = normalize_predictions(model.predict(X_val_enc))
            oof.loc[val_index] = preds

        pred_col = f"{parent_target}_pred"
        parent_df[pred_col] = oof
        prior_oof_cols.append(pred_col)

    return parent_df

def compute_priority_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray],
    priority_metrics: List[str],
) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    y_pred_norm = normalize_predictions(y_pred)
    for metric_name in priority_metrics:
        scorer = METRIC_NAME_TO_SCORER.get(metric_name, "f1")
        json_key = METRIC_NAME_TO_JSON_KEY.get(metric_name, metric_name.lower().replace("-", "_"))
        value = score_predictions(y_true, y_pred_norm, y_proba, scorer)
        metrics[json_key] = float(value)
    return metrics

def optimize_target(
    target: str,
    X: pd.DataFrame,
    y: pd.Series,
    parent_predictions: Optional[pd.DataFrame] = None,
) -> Tuple[str, Dict[str, Any], float]:
    print(f"Starting Optuna optimization for target={target}", flush=True)

    def objective(trial: optuna.Trial) -> float:
        model_name = trial.suggest_categorical("model_name", list(BASE_HYPERPARAMETER_SPACES.keys()))
        params = suggest_hyperparameters(trial, model_name)
        try:
            cv_score = cross_validate_model(
                X, y, model_name, params, OPTIMIZATION_SCORER, parent_predictions
            )
            print(
                f"Target={target} trial={trial.number} model={model_name} score={cv_score:.6f}",
                flush=True,
            )
            return cv_score
        except Exception as exc:
            print(f"Target={target} trial={trial.number} failed: {exc}", flush=True)
            raise

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=MAX_TRIALS, timeout=OPTUNA_TIMEOUT, catch=(Exception,))

    completed = any(t.state.name == "COMPLETE" for t in study.trials)
    if completed:
        best_params = dict(study.best_params)
        best_score = float(study.best_value)
        model_name = best_params.pop("model_name")
        print(
            f"Target={target} best trial score={best_score:.6f} model={model_name} params={best_params}",
            flush=True,
        )
        return model_name, best_params, best_score

    print(
        f"WARNING: No Optuna trials completed for target={target}; using default hyperparameters",
        flush=True,
    )
    model_name = "LGBMClassifier"
    return model_name, dict(DEFAULT_PARAMS[model_name]), 0.0

def train_final_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    params: Dict[str, Any],
    parent_predictions: Optional[pd.DataFrame] = None,
) -> Tuple[Any, FeatureEncoder, List[str]]:
    feature_cols = list(BASE_FEATURES)
    X_train = X.copy()
    if parent_predictions is not None:
        extra_cols = [c for c in parent_predictions.columns if c not in BASE_FEATURES]
        feature_cols.extend(extra_cols)
        for col in extra_cols:
            X_train[col] = parent_predictions[col].values

    encoder = FeatureEncoder(feature_cols)
    X_enc = encoder.fit_transform(X_train)
    num_classes = int(y.nunique())
    model = build_classifier(model_name, params, num_classes)
    model.fit(X_enc, y.values)
    return model, encoder, feature_cols

def evaluate_final_model(
    model: Any,
    encoder: FeatureEncoder,
    X: pd.DataFrame,
    y: pd.Series,
    parent_predictions: Optional[pd.DataFrame] = None,
) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], float]:
    X_eval = X.copy()
    feature_cols = encoder.columns
    if parent_predictions is not None:
        for col in feature_cols:
            if col not in BASE_FEATURES and col in parent_predictions.columns:
                X_eval[col] = parent_predictions[col].values
    X_enc = encoder.transform(X_eval)
    y_pred = normalize_predictions(model.predict(X_enc))
    y_proba = model.predict_proba(X_enc) if hasattr(model, "predict_proba") else None
    cv_score = score_predictions(y.values, y_pred, y_proba, OPTIMIZATION_SCORER)
    return y_pred, y.values, y_proba, cv_score

def save_metrics(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=to_json_serializable)

def main() -> None:
    print("AutoML training script started", flush=True)
    os.makedirs(_OUTPUT_PATH, exist_ok=True)

    working_df = prepare_base_frame(df)
    print(
        f"Dataset ready: rows={len(working_df)} columns={len(working_df.columns)}",
        flush=True,
    )

    all_target_metrics: Dict[str, Dict[str, Any]] = {}

    print("Phase: training target=especialidad (gating model)", flush=True)
    X_esp, y_esp, le_esp = prepare_xy(working_df, "especialidad")
    esp_model_name, esp_params, esp_cv_score = optimize_target("especialidad", X_esp, y_esp)
    esp_model, esp_encoder, esp_feature_cols = train_final_model(
        X_esp, y_esp, esp_model_name, esp_params
    )
    esp_preds_on_full = pd.Series(
        normalize_predictions(esp_model.predict(esp_encoder.transform(X_esp))),
        index=X_esp.index,
        name="especialidad_pred",
    )
    esp_model_path = os.path.join(_OUTPUT_PATH, "especialidad_model.joblib")
    joblib.dump(
        {
            "model": esp_model,
            "encoder": esp_encoder,
            "target_encoder": le_esp,
            "model_name": esp_model_name,
            "feature_columns": esp_feature_cols,
            "best_params": esp_params,
        },
        esp_model_path,
    )
    print(f"Persisted model: {esp_model_path}", flush=True)

    y_pred_esp, y_true_esp, y_proba_esp, _ = evaluate_final_model(
        esp_model, esp_encoder, X_esp, y_esp
    )
    esp_metrics_payload = {
        "target": "especialidad",
        "model_file": "especialidad_model.joblib",
        "best_params": {"model_name": esp_model_name, **esp_params},
        "optimization_metric": OPTIMIZATION_SCORER,
        "cv_score": float(esp_cv_score),
        "priority_metrics": PRIORITY_METRIC_DISPLAY["especialidad"],
        "metrics": compute_priority_metrics(
            y_true_esp, y_pred_esp, y_proba_esp, PRIORITY_METRIC_DISPLAY["especialidad"]
        ),
    }
    esp_metrics_path = os.path.join(_OUTPUT_PATH, "especialidad_metrics.json")
    save_metrics(esp_metrics_path, esp_metrics_payload)
    print(f"Persisted metrics: {esp_metrics_path}", flush=True)
    all_target_metrics["especialidad"] = esp_metrics_payload
    save_metrics(
        os.path.join(_OUTPUT_PATH, "metrics.json"),
        {"targets": all_target_metrics},
    )

    print("Phase: training target=sala (dependent on especialidad)", flush=True)
    X_sala, y_sala, le_sala = prepare_xy(working_df, "sala")
    sala_parent_cv = build_parent_predictions_for_cv(
        working_df.loc[X_sala.index],
        ["especialidad"],
        [esp_model_name],
        [esp_params],
        [le_esp],
    )
    sala_model_name, sala_params, sala_cv_score = optimize_target(
        "sala", X_sala, y_sala, sala_parent_cv
    )
    sala_parent_full = pd.DataFrame(index=X_sala.index)
    sala_parent_full["especialidad_pred"] = esp_preds_on_full.loc[X_sala.index].values
    sala_model, sala_encoder, sala_feature_cols = train_final_model(
        X_sala,
        y_sala,
        sala_model_name,
        sala_params,
        sala_parent_full,
    )
    sala_eval_frame = X_sala.copy()
    sala_eval_frame["especialidad_pred"] = sala_parent_full["especialidad_pred"].values
    sala_preds_on_full = pd.Series(
        normalize_predictions(sala_model.predict(sala_encoder.transform(sala_eval_frame))),
        index=X_sala.index,
        name="sala_pred",
    )
    sala_model_path = os.path.join(_OUTPUT_PATH, "sala_model.joblib")
    joblib.dump(
        {
            "model": sala_model,
            "encoder": sala_encoder,
            "target_encoder": le_sala,
            "model_name": sala_model_name,
            "feature_columns": sala_feature_cols,
            "best_params": sala_params,
            "parent_targets": ["especialidad"],
        },
        sala_model_path,
    )
    print(f"Persisted model: {sala_model_path}", flush=True)

    y_pred_sala, y_true_sala, y_proba_sala, _ = evaluate_final_model(
        sala_model,
        sala_encoder,
        X_sala,
        y_sala,
        sala_parent_full,
    )
    sala_metrics_payload = {
        "target": "sala",
        "model_file": "sala_model.joblib",
        "best_params": {"model_name": sala_model_name, **sala_params},
        "optimization_metric": OPTIMIZATION_SCORER,
        "cv_score": float(sala_cv_score),
        "priority_metrics": PRIORITY_METRIC_DISPLAY["sala"],
        "metrics": compute_priority_metrics(
            y_true_sala, y_pred_sala, y_proba_sala, PRIORITY_METRIC_DISPLAY["sala"]
        ),
    }
    sala_metrics_path = os.path.join(_OUTPUT_PATH, "sala_metrics.json")
    save_metrics(sala_metrics_path, sala_metrics_payload)
    print(f"Persisted metrics: {sala_metrics_path}", flush=True)
    all_target_metrics["sala"] = sala_metrics_payload
    save_metrics(
        os.path.join(_OUTPUT_PATH, "metrics.json"),
        {"targets": all_target_metrics},
    )

    print("Phase: training target=prioridad (dependent on especialidad and sala)", flush=True)
    X_prior, y_prior, le_prior = prepare_xy(working_df, "prioridad")
    prior_parent_full = pd.DataFrame(index=X_prior.index)
    prior_parent_full["especialidad_pred"] = esp_preds_on_full.loc[X_prior.index].values
    prior_parent_full["sala_pred"] = sala_preds_on_full.loc[X_prior.index].values

    prior_parent_cv = build_parent_predictions_for_cv(
        working_df.loc[X_prior.index],
        ["especialidad", "sala"],
        [esp_model_name, sala_model_name],
        [esp_params, sala_params],
        [le_esp, le_sala],
    )
    prior_model_name, prior_params, prior_cv_score = optimize_target(
        "prioridad",
        X_prior,
        y_prior,
        prior_parent_cv,
    )
    prior_model, prior_encoder, prior_feature_cols = train_final_model(
        X_prior,
        y_prior,
        prior_model_name,
        prior_params,
        prior_parent_full,
    )
    prior_model_path = os.path.join(_OUTPUT_PATH, "prioridad_model.joblib")
    joblib.dump(
        {
            "model": prior_model,
            "encoder": prior_encoder,
            "target_encoder": le_prior,
            "model_name": prior_model_name,
            "feature_columns": prior_feature_cols,
            "best_params": prior_params,
            "parent_targets": ["especialidad", "sala"],
        },
        prior_model_path,
    )
    print(f"Persisted model: {prior_model_path}", flush=True)

    y_pred_prior, y_true_prior, y_proba_prior, _ = evaluate_final_model(
        prior_model,
        prior_encoder,
        X_prior,
        y_prior,
        prior_parent_full,
    )
    prior_metrics_payload = {
        "target": "prioridad",
        "model_file": "prioridad_model.joblib",
        "best_params": {"model_name": prior_model_name, **prior_params},
        "optimization_metric": OPTIMIZATION_SCORER,
        "cv_score": float(prior_cv_score),
        "priority_metrics": PRIORITY_METRIC_DISPLAY["prioridad"],
        "metrics": compute_priority_metrics(
            y_true_prior, y_pred_prior, y_proba_prior, PRIORITY_METRIC_DISPLAY["prioridad"]
        ),
    }
    prior_metrics_path = os.path.join(_OUTPUT_PATH, "prioridad_metrics.json")
    save_metrics(prior_metrics_path, prior_metrics_payload)
    print(f"Persisted metrics: {prior_metrics_path}", flush=True)
    all_target_metrics["prioridad"] = prior_metrics_payload
    save_metrics(
        os.path.join(_OUTPUT_PATH, "metrics.json"),
        {"targets": all_target_metrics},
    )

    print("AutoML training completed successfully", flush=True)

if __name__ == "__main__":
    main()