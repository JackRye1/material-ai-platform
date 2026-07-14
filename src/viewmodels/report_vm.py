"""レポート画面の ViewModel。"""
from __future__ import annotations

from typing import List

from PySide6.QtCore import QObject, Signal

from src.core.context import AppContext
from src.viewmodels.task_runner import TaskRunner


class ReportViewModel(QObject):
    exported = Signal(str)   # 出力ファイルパス
    error = Signal(str)

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.runner = TaskRunner(self)

    def export_html(self, sections: List[str]) -> None:
        self.runner.run(
            self.ctx.report.export_html,
            args=(self.ctx.current_dataset, self.ctx.last_train_result, sections),
            on_done=lambda p: self.exported.emit(str(p)),
            on_error=self.error.emit,
        )

    def export_excel(self) -> None:
        self.runner.run(
            self.ctx.report.export_excel,
            args=(self.ctx.current_dataset, self.ctx.last_train_result),
            on_done=lambda p: self.exported.emit(str(p)),
            on_error=self.error.emit,
        )
