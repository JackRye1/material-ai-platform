"""学習・予測・モデル永続化のオーケストレーション。Qt 非依存。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.database.model_registry import ModelRegistry
from src.models.dataset import Dataset
from src.models.model_info import ModelInfo
from src.services.prediction import evaluator
from src.services.prediction.base_predictor import BasePredictor, create_predictor

# モデル実装の登録(import が register_predictor を実行する)
from src.services.prediction import xgboost_predictor  # noqa: F401


@dataclass
class TrainResult:
    predictor: BasePredictor
    model_type: str
    target_name: str
    feature_names: List[str]
    dataset_name: str
    metrics: Dict[str, float]
    importance: Dict[str, float]
    y_test: np.ndarray
    y_pred: np.ndarray
    params: Dict[str, object] = field(default_factory=dict)

    @property
    def residuals(self) -> np.ndarray:
        return self.y_test - self.y_pred


class PredictionService:
    def __init__(self, registry: ModelRegistry, models_dir: Path) -> None:
        self.registry = registry
        self.models_dir = models_dir

    def train(
        self,
        dataset: Dataset,
        target_name: str,
        feature_names: List[str],
        model_type: str = "xgboost",
        params: Optional[Dict[str, object]] = None,
        test_ratio: float = 0.2,
    ) -> TrainResult:
        if not feature_names:
            raise ValueError("特徴量が選択されていません")
        if target_name in feature_names:
            raise ValueError("目的変数は特徴量に含められません")

        data = dataset.df[feature_names + [target_name]].dropna()
        if len(data) < 10:
            raise ValueError(f"有効データが不足しています ({len(data)} 行)。最低 10 行必要です")

        X, y = data[feature_names], data[target_name]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_ratio, random_state=42
        )

        predictor = create_predictor(model_type, params or {})
        predictor.fit(X_train, y_train)
        y_pred = predictor.predict(X_test)

        return TrainResult(
            predictor=predictor,
            model_type=model_type,
            target_name=target_name,
            feature_names=feature_names,
            dataset_name=dataset.name,
            metrics=evaluator.evaluate(y_test.to_numpy(), y_pred),
            importance=predictor.feature_importance(),
            y_test=y_test.to_numpy(),
            y_pred=np.asarray(y_pred),
            params=dict(predictor.params),
        )

    def save_model(self, result: TrainResult, name: str) -> ModelInfo:
        file_path = self.models_dir / f"{uuid4().hex}.joblib"
        result.predictor.save(file_path)
        info = ModelInfo(
            name=name,
            model_type=result.model_type,
            target_name=result.target_name,
            feature_names=result.feature_names,
            metrics=result.metrics,
            params=result.params,
            file_path=str(file_path),
            dataset_name=result.dataset_name,
        )
        self.registry.add(info)
        return info

    def load_model(self, model_id: int) -> "tuple[ModelInfo, BasePredictor]":
        info = self.registry.get(model_id)
        if info is None:
            raise ValueError(f"モデルが見つかりません (id={model_id})")
        path = Path(info.file_path)
        if not path.exists():
            raise FileNotFoundError(f"モデルファイルが見つかりません: {path}")
        predictor = create_predictor(info.model_type, info.params)
        predictor = type(predictor).load(path)
        return info, predictor

    @staticmethod
    def predict(predictor: BasePredictor, df: pd.DataFrame) -> np.ndarray:
        return predictor.predict(df)
