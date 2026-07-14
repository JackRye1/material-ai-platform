"""データプレビューウィジェット(先頭 50 行)。"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.ui.widgets.dashboard_widget import DashboardWidget
from src.ui.widgets.data_table import DataTableView


class PreviewWidget(DashboardWidget):
    widget_id = "preview"

    def build_ui(self, body: QWidget) -> None:
        layout = QVBoxLayout(body)
        layout.setContentsMargins(4, 4, 4, 4)
        self.table = DataTableView()
        layout.addWidget(self.table)
        self.refresh()

    def subscribe(self) -> None:
        self.ctx.events.dataset_changed.connect(lambda *_: self.refresh())

    def refresh(self) -> None:
        ds = self.ctx.current_dataset
        if ds is not None:
            self.table.set_df(ds.df.head(50))
