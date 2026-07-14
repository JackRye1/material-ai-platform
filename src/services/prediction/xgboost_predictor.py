"""XGBoost 回帰モデル(MVP の標準モデル)。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.services.prediction.base_predictor import BasePredictor, register_predictor


class XGBoostPredictor(BasePredictor):
    model_type = "xgboost"

    DEFAULT_PARAMS = {
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.1,
    }

    def __init__(self, params: Dict[str, object]) -> None:
        merged = {**self.DEFAULT_PARAMS, **params}
        super().__init__(merged)
        self.model = XGBRegressor(random_state=42, **merged)
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.feature_names = list(X.columns)
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X[self.feature_names])

    def feature_importance(self) -> Dict[str, float]:
        importances = self.model.feature_importances_
        pairs = sorted(
            zip(self.feature_names, importances), key=lambda p: p[1], reverse=True
        )
        return {name: float(v) for name, v in pairs}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"model": self.model, "params": self.params, "features": self.feature_names},
            path,
        )

    @classmethod
    def load(cls, path: Path) -> "XGBoostPredictor":
        data = joblib.load(path)
        obj = cls(data["params"])
        obj.model = data["model"]
        obj.feature_names = data["features"]
        return obj


register_predictor("xgboost", XGBoostPredictor)
