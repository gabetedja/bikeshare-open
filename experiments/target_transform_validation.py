"""Compare HGB targets on validation dates and print scores in ride counts."""
import json
from math import isfinite

import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import TARGET, VALID_END
from src.features import build_features, feature_columns
from src.ingest import load_raw
from src.train import MODELS, temporal_split


def evaluate() -> dict:
    raw = load_raw()
    features = build_features(raw.loc[raw.dteday <= VALID_END])
    train, valid, _ = temporal_split(features)
    cols = feature_columns(features)
    y_train, y_valid = train[TARGET], valid[TARGET]
    scale_train, scale_valid = train["cnt_roll_7"], valid["cnt_roll_7"]
    if any(not isfinite(x) or x <= 0 for x in pd.concat([scale_train, scale_valid])):
        raise ValueError("Trailing seven-day means must be finite and positive")

    def score(predictions):
        return {
            "r2": round(float(r2_score(y_valid, predictions)), 4),
            "mae": round(float(mean_absolute_error(y_valid, predictions)), 1),
        }

    scores = {}
    for name, model in MODELS.items():
        fitted = clone(model).fit(train[cols], y_train)
        scores[name] = score(fitted.predict(valid[cols]))

    ratio = clone(MODELS["hgb"]).fit(train[cols], y_train / scale_train)
    scores["hgb_ratio"] = score(ratio.predict(valid[cols]) * scale_valid)
    residual = clone(MODELS["hgb"]).fit(train[cols], y_train - scale_train)
    scores["hgb_residual"] = score(residual.predict(valid[cols]) + scale_valid)

    return {
        "n_train": len(train),
        "n_valid": len(valid),
        "train_mean_rides": round(float(y_train.mean()), 1),
        "valid_mean_rides": round(float(y_valid.mean()), 1),
        "train_mean_ratio": round(float((y_train / scale_train).mean()), 4),
        "valid_mean_ratio": round(float((y_valid / scale_valid).mean()), 4),
        "validation": scores,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
