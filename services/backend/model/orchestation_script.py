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
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import cohen_kappa_score, f1_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from xgboost import XGBClassifier

optuna.logging.set_verbosity(optuna.logging.WARNING)

_OUTPUT_PATH = os.environ.get("OUTPUT_PATH", ".")
_DATASET_PATH = os.environ.get("DATASET_PATH", "/app/uploads/datos_limpios.xlsx")

FEATURE_COLS = ["descrip", "edad", "sospechadiag", "datosclini"]
GATE_TARGET = "especialidad"
DEPENDENT_TARGETS = ["prioridad", "sala"]
ALL_TARGETS = [GATE_TARGET] + DEPENDENT_TARGETS

PRIORIDAD_MAPPING = {"A": 0, "B": 1, "C": 2}

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
        "learning_rate": 0.1,
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
        "learning_rate": 0.1,
        "max_depth": 5,
        "n_estimators": 100,
        "subsample": 0.9,
    },
}

TARGETS_EVALUATION = {
    "especialidad": {
        "priority_metrics": ["F1-Score", "Recall", "Kappa"],
    },
    "prioridad": {
        "priority_metrics": ["F1-Score", "Kappa"],
    },
    "sala": {
        "priority_metrics": ["Kappa", "F1-Score"],
    },
}

METRIC_TO_SCORER = {
    "F1-Score": "f1",
    "Recall": "recall",
    "Kappa": "kappa",
}

METRIC_TO_SNAKE = {
    "F1-Score": "f1_score",
    "Recall": "recall",
    "Kappa": "kappa",
}

CV_FOLDS = 2
MAX_TRIALS = 5
OPTUNA_TIMEOUT = 60
RANDOM_STATE = 42

MODEL_CLASSES = {
    "LGBMClassifier": LGBMClassifier,
    "RandomForestClassifier": RandomForestClassifier,
    "XGBClassifier": XGBClassifier,
}

_DEFAULT_METRIC_FUNCTIONS = {
    "f1": f1_score,
    "recall": recall_score,
    "kappa": cohen_kappa_score,
}

try:
    resolve_metric
except NameError:
    def resolve_metric(scorer):
        funcs = globals().get("METRIC_FUNCTIONS", _DEFAULT_METRIC_FUNCTIONS)
        return funcs[scorer]

def ensure_output_dir() -> None:
    os.makedirs(_OUTPUT_PATH, exist_ok=True)

def load_dataframe() -> pd.DataFrame:
    if "df" in globals() and isinstance(globals()["df"], pd.DataFrame):
        data = globals()["df"].copy()
        print(f"Using pre-loaded dataframe with shape {data.shape}", flush=True)
        return data
    print(f"Loading dataset from {_DATASET_PATH}", flush=True)
    data = pd.read_excel(_DATASET_PATH)
    print(f"Loaded dataset with shape {data.shape}", flush=True)
    return data

def prepare_features(data: pd.DataFrame) -> pd.DataFrame:
    work = data.copy()
    if "edad" in work.columns:
        work["edad"] = pd.to_numeric(work["edad"], errors="coerce")
    for col in FEATURE_COLS:
        if col in work.columns and col != "edad":
            work[col] = work[col].astype(str).str.strip()
    return work

def get_numeric_and_categorical_cols(feature_cols: List[str], frame: pd.DataFrame) -> Tuple[List[str], List[str]]:
    numeric_cols = [c for c in feature_cols if c in frame.columns and pd.api.types.is_numeric_dtype(frame[c])]
    categorical_cols = [c for c in feature_cols if c in frame.columns and c not in numeric_cols]
    return numeric_cols, categorical_cols

def build_preprocessor(feature_cols: List[str], frame: pd.DataFrame) -> ColumnTransformer:
    numeric_cols, categorical_cols = get_numeric_and_categorical_cols(feature_cols, frame)
    transformers = []
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                                dtype=np.float64,
                            ),
                        ),
                    ]
                ),
                categorical_cols,
            )
        )
    if numeric_cols:
        transformers.append(("num", SimpleImputer(strategy="median"), numeric_cols))
    return ColumnTransformer(transformers=transformers, remainder="drop")

def encode_target(target_name: str, y_raw: pd.Series) -> Tuple[pd.Series, Optional[LabelEncoder]]:
    if target_name == "prioridad":
        mapped = y_raw.astype(str).str.strip().map(PRIORIDAD_MAPPING)
        encoded = pd.Series(mapped.values, index=y_raw.index, dtype="float64")
        return encoded, None
    encoder = LabelEncoder()
    encoded_values = encoder.fit_transform(y_raw.astype(str).str.strip())
    encoded = pd.Series(encoded_values, index=y_raw.index)
    return encoded, encoder

def suggest_params(trial: optuna.Trial, model_name: str) -> Dict[str, Any]:
    space = BASE_HYPERPARAMETER_SPACES[model_name]
    params: Dict[str, Any] = {}
    for key, values in space.items():
        params[key] = trial.suggest_categorical(key, values)
    return params

def create_classifier(model_name: str, params: Dict[str, Any], n_classes: int) -> Any:
    model_params = dict(params)
    if model_name == "LGBMClassifier":
        model_params.update(
            {
                "objective": "multiclass" if n_classes > 2 else "binary",
                "num_class": n_classes if n_classes > 2 else 1,
                "random_state": RANDOM_STATE,
                "n_jobs": -1,
                "verbosity": -1,
            }
        )
    elif model_name == "XGBClassifier":
        model_params.update(
            {
                "objective": "multi:softprob" if n_classes > 2 else "binary:logistic",
                "num_class": n_classes if n_classes > 2 else None,
                "random_state": RANDOM_STATE,
                "n_jobs": -1,
                "eval_metric": "mlogloss" if n_classes > 2 else "logloss",
                "use_label_encoder": False,
            }
        )
        if n_classes <= 2:
            model_params.pop("num_class", None)
    elif model_name == "RandomForestClassifier":
        model_params.update({"random_state": RANDOM_STATE, "n_jobs": -1})
    return MODEL_CLASSES[model_name](**model_params)

def metric_kwargs(scorer: str, n_classes: int) -> Dict[str, Any]:
    if scorer in ("f1", "precision", "recall"):
        if n_classes > 2:
            return {"average": "weighted"}
        return {"average": "binary"}
    return {}

def score_predictions(
    scorer: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int,
) -> float:
    metric_fn = resolve_metric(scorer)
    kwargs = metric_kwargs(scorer, n_classes)
    return float(metric_fn(y_true, y_pred, **kwargs))

def compute_all_priority_metrics(
    priority_metrics: List[str],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int,
) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    for metric_name in priority_metrics:
        scorer = METRIC_TO_SCORER[metric_name]
        snake_name = METRIC_TO_SNAKE[metric_name]
        value = score_predictions(scorer, y_true, y_pred, n_classes)
        metrics[snake_name] = value
    return metrics

def cross_val_score_model(
    model_name: str,
    params: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
    preprocessor: ColumnTransformer,
    scorer: str,
    n_classes: int,
) -> float:
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores: List[float] = []
    y_values = y.values
    for train_idx, val_idx in skf.split(X, y_values):
        X_train = X.iloc[train_idx]
        X_val = X.iloc[val_idx]
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]
        fold_preprocessor = build_preprocessor(list(X.columns), X_train)
        fold_preprocessor.fit(X_train)
        X_train_t = fold_preprocessor.transform(X_train)
        X_val_t = fold_preprocessor.transform(X_val)
        model = create_classifier(model_name, params, n_classes)
        model.fit(X_train_t, y_train.values)
        y_pred = model.predict(X_val_t)
        scores.append(score_predictions(scorer, y_val.values, y_pred, n_classes))
    return float(np.mean(scores))

def cross_val_score_gated_model(
    model_name: str,
    params: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
    gate_X: pd.DataFrame,
    gate_y: pd.Series,
    gate_model_name: str,
    gate_params: Dict[str, Any],
    gate_n_classes: int,
    scorer: str,
    n_classes: int,
) -> float:
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores: List[float] = []
    y_values = y.values
    for train_idx, val_idx in skf.split(X, y_values):
        X_train = X.iloc[train_idx]
        X_val = X.iloc[val_idx]
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]
        gate_train = gate_X.iloc[train_idx]
        gate_val = gate_X.iloc[val_idx]
        gate_y_train = gate_y.iloc[train_idx]

        gate_preprocessor = build_preprocessor(list(gate_X.columns), gate_train)
        gate_preprocessor.fit(gate_train)
        gate_train_t = gate_preprocessor.transform(gate_train)
        gate_val_t = gate_preprocessor.transform(gate_val)
        gate_model = create_classifier(gate_model_name, gate_params, gate_n_classes)
        gate_model.fit(gate_train_t, gate_y_train.values)
        gate_pred_train = gate_model.predict(gate_train_t)
        gate_pred_val = gate_model.predict(gate_val_t)

        X_train_aug = X_train.copy()
        X_val_aug = X_val.copy()
        X_train_aug["especialidad_pred"] = gate_pred_train
        X_val_aug["especialidad_pred"] = gate_pred_val

        fold_preprocessor = build_preprocessor(list(X_train_aug.columns), X_train_aug)
        fold_preprocessor.fit(X_train_aug)
        X_train_t = fold_preprocessor.transform(X_train_aug)
        X_val_t = fold_preprocessor.transform(X_val_aug)
        model = create_classifier(model_name, params, n_classes)
        model.fit(X_train_t, y_train.values)
        y_pred = model.predict(X_val_t)
        scores.append(score_predictions(scorer, y_val.values, y_pred, n_classes))
    return float(np.mean(scores))

def run_optuna_for_model(
    model_name: str,
    X: pd.DataFrame,
    y: pd.Series,
    scorer: str,
    n_classes: int,
    gate_bundle: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], float]:
    def objective(trial: optuna.Trial) -> float:
        params = suggest_params(trial, model_name)
        if gate_bundle is None:
            score = cross_val_score_model(
                model_name,
                params,
                X,
                y,
                build_preprocessor(list(X.columns), X),
                scorer,
                n_classes,
            )
        else:
            score = cross_val_score_gated_model(
                model_name,
                params,
                X,
                y,
                gate_bundle["X"],
                gate_bundle["y"],
                gate_bundle["model_name"],
                gate_bundle["params"],
                gate_bundle["n_classes"],
                scorer,
                n_classes,
            )
        print(
            f"  Optuna trial {trial.number} ({model_name}): score={score:.6f}",
            flush=True,
        )
        return score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=MAX_TRIALS, timeout=OPTUNA_TIMEOUT, catch=(Exception,))
    has_complete = any(t.state.name == "COMPLETE" for t in study.trials)
    if has_complete:
        return study.best_params, float(study.best_value)
    print(
        f"Warning: no completed Optuna trials for {model_name}; using default hyperparameters",
        flush=True,
    )
    default_score = (
        cross_val_score_model(
            model_name,
            DEFAULT_PARAMS[model_name],
            X,
            y,
            build_preprocessor(list(X.columns), X),
            scorer,
            n_classes,
        )
        if gate_bundle is None
        else cross_val_score_gated_model(
            model_name,
            DEFAULT_PARAMS[model_name],
            X,
            y,
            gate_bundle["X"],
            gate_bundle["y"],
            gate_bundle["model_name"],
            gate_bundle["params"],
            gate_bundle["n_classes"],
            scorer,
            n_classes,
        )
    )
    return DEFAULT_PARAMS[model_name], float(default_score)

def select_best_model(
    target_name: str,
    X: pd.DataFrame,
    y: pd.Series,
    gate_bundle: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], float, str]:
    priority_metrics = TARGETS_EVALUATION[target_name]["priority_metrics"]
    scorer = METRIC_TO_SCORER[priority_metrics[0]]
    n_classes = int(y.nunique())
    print(f"Starting model competition for target '{target_name}'", flush=True)
    best_model_name = None
    best_params: Dict[str, Any] = {}
    best_score = float("-inf")
    for model_name in MODEL_CLASSES:
        print(f"Optimizing {model_name} for target '{target_name}'", flush=True)
        params, score = run_optuna_for_model(
            model_name,
            X,
            y,
            scorer,
            n_classes,
            gate_bundle=gate_bundle,
        )
        print(
            f"Best {model_name} for '{target_name}': score={score:.6f}, params={params}",
            flush=True,
        )
        if score > best_score:
            best_score = score
            best_model_name = model_name
            best_params = params
    assert best_model_name is not None
    return best_model_name, best_params, best_score, scorer

def augment_with_gate_predictions(
    X: pd.DataFrame,
    gate_preprocessor: ColumnTransformer,
    gate_model: Any,
) -> pd.DataFrame:
    X_aug = X.copy()
    gate_features = gate_preprocessor.feature_names_in_
    gate_input = X[list(gate_features)]
    gate_transformed = gate_preprocessor.transform(gate_input)
    X_aug["especialidad_pred"] = gate_model.predict(gate_transformed)
    return X_aug

def train_final_model(
    model_name: str,
    params: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
) -> Tuple[ColumnTransformer, Any]:
    preprocessor = build_preprocessor(list(X.columns), X)
    preprocessor.fit(X)
    X_t = preprocessor.transform(X)
    n_classes = int(y.nunique())
    model = create_classifier(model_name, params, n_classes)
    model.fit(X_t, y.values)
    return preprocessor, model

def evaluate_model(
    preprocessor: ColumnTransformer,
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    priority_metrics: List[str],
) -> Dict[str, float]:
    X_t = preprocessor.transform(X)
    y_pred = model.predict(X_t)
    n_classes = int(y.nunique())
    return compute_all_priority_metrics(priority_metrics, y.values, y_pred, n_classes)

def write_target_metrics(target_payload: Dict[str, Any]) -> None:
    target_name = target_payload["target"]
    target_path = os.path.join(_OUTPUT_PATH, f"{target_name}_metrics.json")
    with open(target_path, "w", encoding="utf-8") as handle:
        json.dump(target_payload, handle, indent=2)
    print(f"Persisted metrics to {target_path}", flush=True)

def update_aggregate_metrics(all_target_metrics: Dict[str, Dict[str, Any]]) -> None:
    aggregate_path = os.path.join(_OUTPUT_PATH, "metrics.json")
    payload = {"targets": all_target_metrics}
    with open(aggregate_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Updated aggregate metrics at {aggregate_path}", flush=True)

def to_json_serializable(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {k: to_json_serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_json_serializable(v) for v in value]
    return value

def main() -> None:
    print("AutoML GatedChain training script started", flush=True)
    ensure_output_dir()

    data = load_dataframe()
    data = prepare_features(data)
    print(
        f"Dataset ready: {data.shape[0]} rows, {data.shape[1]} columns",
        flush=True,
    )

    all_target_metrics: Dict[str, Dict[str, Any]] = {}
    gate_artifacts: Dict[str, Any] = {}

    print(f"Phase 1: training gate target '{GATE_TARGET}'", flush=True)
    X_gate = data[FEATURE_COLS].copy()
    y_gate_raw = data[GATE_TARGET]
    valid_gate = y_gate_raw.notna()
    X_gate = X_gate.loc[valid_gate]
    y_gate_raw = y_gate_raw.loc[valid_gate]
    assert y_gate_raw.notna().all()
    y_gate, gate_label_encoder = encode_target(GATE_TARGET, y_gate_raw)
    valid_gate = y_gate.notna()
    X_gate = X_gate.loc[valid_gate]
    y_gate = y_gate.loc[valid_gate]
    assert y_gate.notna().all()

    gate_model_name, gate_params, gate_cv_score, gate_scorer = select_best_model(
        GATE_TARGET,
        X_gate,
        y_gate,
    )
    gate_preprocessor, gate_model = train_final_model(
        gate_model_name,
        gate_params,
        X_gate,
        y_gate,
    )
    gate_metrics = evaluate_model(
        gate_preprocessor,
        gate_model,
        X_gate,
        y_gate,
        TARGETS_EVALUATION[GATE_TARGET]["priority_metrics"],
    )
    gate_model_file = f"{GATE_TARGET}_model.joblib"
    gate_bundle = {
        "target": GATE_TARGET,
        "model_name": gate_model_name,
        "params": gate_params,
        "preprocessor": gate_preprocessor,
        "model": gate_model,
        "label_encoder": gate_label_encoder,
        "feature_cols": list(X_gate.columns),
    }
    joblib.dump(gate_bundle, os.path.join(_OUTPUT_PATH, gate_model_file))
    print(f"Persisted gate model to {gate_model_file}", flush=True)

    gate_payload = to_json_serializable(
        {
            "target": GATE_TARGET,
            "model_file": gate_model_file,
            "best_params": gate_params,
            "optimization_metric": gate_scorer,
            "cv_score": gate_cv_score,
            "priority_metrics": TARGETS_EVALUATION[GATE_TARGET]["priority_metrics"],
            "metrics": gate_metrics,
        }
    )
    write_target_metrics(gate_payload)
    all_target_metrics[GATE_TARGET] = gate_payload
    update_aggregate_metrics(all_target_metrics)

    gate_artifacts = {
        "X": X_gate,
        "y": y_gate,
        "model_name": gate_model_name,
        "params": gate_params,
        "n_classes": int(y_gate.nunique()),
        "preprocessor": gate_preprocessor,
        "model": gate_model,
    }

    for target_name in DEPENDENT_TARGETS:
        print(f"Phase 2: training dependent target '{target_name}'", flush=True)
        X_base = data[FEATURE_COLS].copy()
        y_raw = data[target_name]
        valid = y_raw.notna()
        X_base = X_base.loc[valid]
        y_raw = y_raw.loc[valid]
        assert y_raw.notna().all()
        y_target, label_encoder = encode_target(target_name, y_raw)
        valid = y_target.notna()
        X_base = X_base.loc[valid]
        y_target = y_target.loc[valid]
        assert y_target.notna().all()

        gate_y_aligned, _ = encode_target(GATE_TARGET, data.loc[X_base.index, GATE_TARGET])
        valid_aligned = gate_y_aligned.notna()
        X_base = X_base.loc[valid_aligned]
        y_target = y_target.loc[valid_aligned]
        gate_y_aligned = gate_y_aligned.loc[valid_aligned]
        assert y_target.notna().all()

        gate_bundle_cv = {
            "X": X_base.copy(),
            "y": gate_y_aligned,
            "model_name": gate_model_name,
            "params": gate_params,
            "n_classes": gate_artifacts["n_classes"],
        }

        model_name, best_params, cv_score, scorer = select_best_model(
            target_name,
            X_base,
            y_target,
            gate_bundle=gate_bundle_cv,
        )
        X_aug = augment_with_gate_predictions(
            X_base,
            gate_preprocessor,
            gate_model,
        )
        preprocessor, model = train_final_model(model_name, best_params, X_aug, y_target)
        metrics = evaluate_model(
            preprocessor,
            model,
            X_aug,
            y_target,
            TARGETS_EVALUATION[target_name]["priority_metrics"],
        )
        model_file = f"{target_name}_model.joblib"
        artifact = {
            "target": target_name,
            "model_name": model_name,
            "params": best_params,
            "preprocessor": preprocessor,
            "model": model,
            "label_encoder": label_encoder,
            "feature_cols": list(X_aug.columns),
            "gate_target": GATE_TARGET,
            "gate_model_file": gate_model_file,
        }
        joblib.dump(artifact, os.path.join(_OUTPUT_PATH, model_file))
        print(f"Persisted model to {model_file}", flush=True)

        target_payload = to_json_serializable(
            {
                "target": target_name,
                "model_file": model_file,
                "best_params": best_params,
                "optimization_metric": scorer,
                "cv_score": cv_score,
                "priority_metrics": TARGETS_EVALUATION[target_name]["priority_metrics"],
                "metrics": metrics,
            }
        )
        write_target_metrics(target_payload)
        all_target_metrics[target_name] = target_payload
        update_aggregate_metrics(all_target_metrics)

    print("AutoML GatedChain training completed successfully", flush=True)

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
# --- EXECUTION OUTPUT ---
Dataset loaded: 10240 rows, 7 columns
AutoML GatedChain training script started
Using pre-loaded dataframe with shape (10240, 7)
Dataset ready: 10240 rows, 7 columns
Phase 1: training gate target 'especialidad'
Starting model competition for target 'especialidad'
Optimizing LGBMClassifier for target 'especialidad'
  Optuna trial 0 (LGBMClassifier): score=1.000000
  Optuna trial 1 (LGBMClassifier): score=1.000000
  Optuna trial 2 (LGBMClassifier): score=1.000000
  Optuna trial 3 (LGBMClassifier): score=1.000000
  Optuna trial 4 (LGBMClassifier): score=1.000000
Best LGBMClassifier for 'especialidad': score=1.000000, params={'learning_rate': 0.1, 'max_depth': 7, 'n_estimators': 300, 'num_leaves': 31, 'subsample': 0.85}
Optimizing RandomForestClassifier for target 'especialidad'
  Optuna trial 0 (RandomForestClassifier): score=1.000000
  Optuna trial 1 (RandomForestClassifier): score=1.000000
  Optuna trial 2 (RandomForestClassifier): score=1.000000
  Optuna trial 3 (RandomForestClassifier): score=1.000000
  Optuna trial 4 (RandomForestClassifier): score=1.000000
Best RandomForestClassifier for 'especialidad': score=1.000000, params={'max_depth': 20, 'max_features': 'log2', 'min_samples_split': 2, 'n_estimators': 300}
Optimizing XGBClassifier for target 'especialidad'
  Optuna trial 0 (XGBClassifier): score=1.000000
  Optuna trial 1 (XGBClassifier): score=1.000000
  Optuna trial 2 (XGBClassifier): score=1.000000
  Optuna trial 3 (XGBClassifier): score=1.000000
  Optuna trial 4 (XGBClassifier): score=1.000000
Best XGBClassifier for 'especialidad': score=1.000000, params={'colsample_bytree': 0.9, 'learning_rate': 0.01, 'max_depth': 7, 'n_estimators': 500, 'subsample': 0.9}
Persisted gate model to especialidad_model.joblib
Persisted metrics to /app/model/especialidad_metrics.json
Updated aggregate metrics at /app/model/metrics.json
Phase 2: training dependent target 'prioridad'
Starting model competition for target 'prioridad'
Optimizing LGBMClassifier for target 'prioridad'
  Optuna trial 0 (LGBMClassifier): score=0.571823
  Optuna trial 1 (LGBMClassifier): score=0.564875
Best LGBMClassifier for 'prioridad': score=0.571823, params={'learning_rate': 0.05, 'max_depth': 5, 'n_estimators': 500, 'num_leaves': 63, 'subsample': 0.85}
Optimizing RandomForestClassifier for target 'prioridad'
  Optuna trial 0 (RandomForestClassifier): score=0.537629
  Optuna trial 1 (RandomForestClassifier): score=0.592046
  Optuna trial 2 (RandomForestClassifier): score=0.549170
  Optuna trial 3 (RandomForestClassifier): score=0.545948
  Optuna trial 4 (RandomForestClassifier): score=0.537629
Best RandomForestClassifier for 'prioridad': score=0.592046, params={'max_depth': 5, 'max_features': 'sqrt', 'min_samples_split': 10, 'n_estimators': 500}
Optimizing XGBClassifier for target 'prioridad'
  Optuna trial 0 (XGBClassifier): score=0.573688
Best XGBClassifier for 'prioridad': score=0.573688, params={'colsample_bytree': 0.9, 'learning_rate': 0.01, 'max_depth': 7, 'n_estimators': 500, 'subsample': 1.0}
Persisted model to prioridad_model.joblib
Persisted metrics to /app/model/prioridad_metrics.json
Updated aggregate metrics at /app/model/metrics.json
Phase 2: training dependent target 'sala'
Starting model competition for target 'sala'
Optimizing LGBMClassifier for target 'sala'
  Optuna trial 0 (LGBMClassifier): score=0.304073
  Optuna trial 1 (LGBMClassifier): score=0.304667
  Optuna trial 2 (LGBMClassifier): score=0.310186
Best LGBMClassifier for 'sala': score=0.310186, params={'learning_rate': 0.1, 'max_depth': 5, 'n_estimators': 100, 'num_leaves': 63, 'subsample': 1.0}
Optimizing RandomForestClassifier for target 'sala'
  Optuna trial 0 (RandomForestClassifier): score=0.264802
  Optuna trial 1 (RandomForestClassifier): score=0.238324
  Optuna trial 2 (RandomForestClassifier): score=0.252621
  Optuna trial 3 (RandomForestClassifier): score=0.280771
  Optuna trial 4 (RandomForestClassifier): score=0.224911
Best RandomForestClassifier for 'sala': score=0.280771, params={'max_depth': 10, 'max_features': 'log2', 'min_samples_split': 10, 'n_estimators': 100}
Optimizing XGBClassifier for target 'sala'
  Optuna trial 0 (XGBClassifier): score=0.283111
  Optuna trial 1 (XGBClassifier): score=0.290718
  Optuna trial 2 (XGBClassifier): score=0.318075
  Optuna trial 3 (XGBClassifier): score=0.297762
  Optuna trial 4 (XGBClassifier): score=0.314668
Best XGBClassifier for 'sala': score=0.318075, params={'colsample_bytree': 1.0, 'learning_rate': 0.05, 'max_depth': 5, 'n_estimators': 500, 'subsample': 0.9}
Persisted model to sala_model.joblib
Persisted metrics to /app/model/sala_metrics.json
Updated aggregate metrics at /app/model/metrics.json
AutoML GatedChain training completed successfully
