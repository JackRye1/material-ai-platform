"""予測モデルの抽象インターフェース。

新しいモデル(RandomForest / LightGBM / ガウス過程など)を追加するときは、
BasePredictor を実装して register_predictor で登録するだけでよい。
UI・サービス層のコード変更は不要。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

_PREDICTOR_FACTORIES: Dict[str, Callable[..., "BasePredictor"]] = {}


def register_predictor(model_type: str, factory: Callable[..., "BasePredictor"]) -> None:
    _PREDICTOR_FACTORIES[model_type] = factory


def create_predictor(model_type: str, params: Dict[str, object]) -> "BasePredictor":
    if model_type not in _PREDICTOR_FACTORIES:
        raise ValueError(f"未登録のモデル種別です: {model_type}")
    return _PREDICTOR_FACTORIES[model_type](params)


def available_predictors() -> List[str]:
    return list(_PREDICTOR_FACTORIES.keys())


class BasePredictor(ABC):
    model_type: str = "base"

    def __init__(self, params: Dict[str, object]) -> None:
        self.params = dict(params)

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...

    @abstractmethod
    def feature_importance(self) -> Dict[str, float]:
        """特徴量名 → 重要度(降順ソート済み)"""

    @abstractmethod
    def save(self, path: Path) -> None: ...

    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> "BasePredictor": ...
