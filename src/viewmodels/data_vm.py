"""データ管理画面の ViewModel。"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.core.context import AppContext
from src.models.dataset import ColumnRole, Dataset
from src.viewmodels.task_runner import TaskRunner


class DataViewModel(QObject):
    dataset_loaded = Signal(object)      # Dataset
    validation_done = Signal(object)     # ValidationResult
    error = Signal(str)

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.runner = TaskRunner(self)

    def import_file(self, path: str) -> None:
        self.runner.run(
            self.ctx.importer.load,
            args=(path,),
            on_done=self._on_imported,
            on_error=self.error.emit,
        )

    def _on_imported(self, dataset: Dataset) -> None:
        self.ctx.set_dataset(dataset)
        self.dataset_loaded.emit(dataset)
        self.validate()

    def validate(self) -> None:
        ds = self.ctx.current_dataset
        if ds is None:
            return
        try:
            self.validation_done.emit(self.ctx.validator.validate(ds))
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))

    def set_role(self, column: str, role_value: str) -> None:
        ds = self.ctx.current_dataset
        if ds is None:
            return
        ds.set_role(column, ColumnRole(role_value))
        self.ctx.events.dataset_changed.emit(ds)

    def save_to_db(self) -> None:
        ds = self.ctx.current_dataset
        if ds is None:
            self.error.emit("保存するデータがありません")
            return
        try:
            self.ctx.dataset_repo.save(ds)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))

    def load_latest_from_db(self) -> None:
        try:
            ds = self.ctx.dataset_repo.load_latest()
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
            return
        if ds is None:
            self.error.emit("データベースに保存済みデータがありません")
            return
        self.ctx.set_dataset(ds)
        self.dataset_loaded.emit(ds)
        self.validate()
