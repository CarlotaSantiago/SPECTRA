import logging
import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from pandas.api.types import is_numeric_dtype, is_float_dtype, is_object_dtype, is_string_dtype
from typing import Dict, Any

logger = logging.getLogger(__name__)

def classify_data(series: pd.Series, n_rows: int) -> Dict[str, Any]:
    nunique = series.nunique()
    ratio = nunique / n_rows

    result = {
        "nunique": nunique,
        "r_ratio": round(ratio, 4),
    }

    if nunique == 2:
        result.update({"technical_level": 1, "subclass": "binary"})
    elif is_numeric_dtype(series) and nunique > 10:
        subclass = "continuous" if is_float_dtype(series) else "discrete"
        result.update({"technical_level": 3, "subclass": subclass})
    elif ratio < 0.05:
        result.update({"technical_level": 2, "subclass": "categorical"})
    elif ratio < 0.8:
        subclass = "continuous" if is_float_dtype(series) else "discrete"
        result.update({"technical_level": 3, "subclass": subclass})
    else:
        result.update({"technical_level": 4, "subclass": "high cardinality"})
    
    return result

def encode_series(series: pd.Series) -> pd.Series:
    if is_object_dtype(series) or is_string_dtype(series):
        return pd.Series(LabelEncoder().fit_transform(series.astype(str)), index=series.index)
    return series

def compute_information_gain_targets(
        df: pd.DataFrame,
        target1: str,
        target2: str,
        col_types: Dict[str, int],
        is_discrete: bool,
        device: torch.device
    ) -> float:
    temp_df = df[[target1, target2]].dropna()
    if temp_df.empty:
        return 0.0

    try:
        X = encode_series(temp_df[target1]).values.reshape(-1, 1)
        y = encode_series(temp_df[target2])
        if col_types[target2] in [1,2]:
            score = mutual_info_classif(X, y, discrete_features=[is_discrete])[0]
        else:
            score = mutual_info_regression(X, y, discrete_features=[is_discrete])[0]

        score = round(float(score), 4)

    except Exception as e:
        logger.warning(f"IG error: {target1} vs {target2} -> {e}")
        score = 0.0
    return score

def compute_information_gain(
    df: pd.DataFrame,
    feature: str,
    targets: list,
    target_meta: Dict[str, str],
    is_discrete: bool,
    device: torch.device
) -> Dict[str, float]:

    scores = {}

    for t in targets:
        temp_df = df[[feature, t]].dropna()

        if temp_df.empty:
            scores[t] = 0.0
            continue

        X = temp_df[[feature]].copy()
        y = temp_df[t].copy()

        try:
            X[feature] = encode_series(X[feature])
            y = encode_series(y)

            if target_meta[t]['technical_level'] in [1,2]:
                score = mutual_info_classif(X, y, discrete_features=is_discrete)[0]
            else:
                score = mutual_info_regression(X, y, discrete_features=is_discrete)[0]

            scores[t] = round(float(score), 4)

        except Exception as e:
            logger.warning(f"IG error: {feature} vs {t} -> {e}")
            scores[t] = 0.0

    return scores
