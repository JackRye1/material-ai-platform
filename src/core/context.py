"""AppContext: サービス・設定・共有状態の入れ物(簡易DIコンテナ)。

ViewModel はこの context 経由でのみサービスへアクセスする。
"""
from __future__ import annotations

from typing import Optional

from src.config.settings import AppSettings
from src.core.events import EventBus
from src.database.connection import Database
from src.database.dataset_repo import DatasetRepo
from src.database.model_registry import ModelRegistry
from src.models.dataset import Dataset
from src.services.analysis.analysis_service import AnalysisService
from src.services.data.importer import DataImporter
from src.services.data.validator import DataValidator
from src.services.prediction.prediction_service import PredictionService, TrainResult
from src.services.report.report_service import ReportService


class AppContext:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.events = EventBus()

        self.db = Database(settings.db_file)
        self.dataset_repo = DatasetRepo(self.db)
        self.model_registry = ModelRegistry(self.db)

        self.importer = DataImporter()
        self.validator = DataValidator()
        self.analysis = AnalysisService()
        self.prediction = PredictionService(self.model_registry, settings.models_path)
        self.report = ReportService(settings.report_path)

        # 共有状態
        self.current_dataset: Optional[Dataset] = None
        self.last_train_result: Optional[TrainResult] = None

    def set_dataset(self, dataset: Dataset) -> None:
        self.current_dataset = dataset
        self.events.dataset_changed.emit(dataset)

    def set_train_result(self, result: "TrainResult") -> None:
        self.last_train_result = result
        self.events.model_trained.emit(result)

    def shutdown(self) -> None:
        self.db.close()
