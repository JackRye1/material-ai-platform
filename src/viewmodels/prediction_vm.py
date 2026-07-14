"""特性予測画面の ViewModel。"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from PySide6.QtCore import QObject, Signal

from src.core.context import AppContext
from src.services.prediction import evaluator
from src.services.prediction.base_predictor import available_predictors
from src.services.prediction.prediction_service import TrainResult
from src.viewmodels.task_runner import TaskRunner


class PredictionViewModel(QObject):
    train_finished = Signal(object)   # TrainResult
    model_saved = Signal(object)      # ModelInfo
    error = Signal(str)

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.runner = TaskRunner(self)

    @staticmethod
    def model_types() -> List[str]:
        return available_predictors()

    def train(
        self,
        target: str,
        features: List[str],
        model_type: str,
        params: Dict[str, object],
        test_ratio: float,
    ) -> None:
        ds = self.ctx.current_dataset
        if ds is None:
            self.error.emit("データが読み込まれていません(データ管理画面で読み込んでください)")
            return
        self.runner.run(
            self.ctx.prediction.train,
            args=(ds, target, features),
            kwargs={"model_type": model_type, "params": params, "test_ratio": test_ratio},
            on_done=self._on_trained,
            on_error=self.error.emit,
        )

    def _on_trained(self, result: TrainResult) -> None:
        self.ctx.set_train_result(result)
        self.train_finished.emit(result)

    def save_model(self, name: str) -> None:
        result = self.ctx.last_train_result
        if result is None:
            self.error.emit("保存する学習結果がありません")
            return
        try:
            info = self.ctx.prediction.save_model(result, name)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
            return
        self.ctx.events.model_registry_changed.emit()
        self.model_saved.emit(info)

    def list_models(self):
        return self.ctx.model_registry.list_all()

    def load_and_evaluate(self, model_id: int) -> None:
        """保存済みモデルを読込み、現在のデータで評価して結果表示する。"""
        ds = self.ctx.current_dataset
        if ds is None:
            self.error.emit("データが読み込まれていません")
            return
        self.runner.run(
            self._load_eval,
            args=(model_id,),
            on_done=self._on_trained,
            on_error=self.error.emit,
        )

    def _load_eval(self, model_id: int) -> TrainResult:
        ds = self.ctx.current_dataset
        info, predictor = self.ctx.prediction.load_model(model_id)
        missing = [c for c in info.feature_names + [info.target_name] if c not in ds.df.columns]
        if missing:
            raise ValueError(f"現在のデータに必要な列がありません: {', '.join(missing)}")
        data = ds.df[info.feature_names + [info.target_name]].dropna()
        y_true = data[info.target_name].to_numpy()
        y_pred = np.asarray(predictor.predict(data[info.feature_names]))
        return TrainResult(
            predictor=predictor,
            model_type=info.model_type,
            target_name=info.target_name,
            feature_names=info.feature_names,
            dataset_name=ds.name,
            metrics=evaluator.evaluate(y_true, y_pred),
            importance=predictor.feature_importance(),
            y_test=y_true,
            y_pred=y_pred,
            params=info.params,
        )
