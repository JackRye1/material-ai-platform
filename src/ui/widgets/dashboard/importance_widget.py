"""重要因子(Feature Importance)ウィジェット。"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.ui.widgets.chart_canvas import ChartCanvas
from src.ui.widgets.dashboard_widget import DashboardWidget


class ImportanceWidget(DashboardWidget):
    widget_id = "importance"

    def build_ui(self, body: QWidget) -> None:
        layout = QVBoxLayout(body)
        layout.setContentsMargins(4, 4, 4, 4)
        self.canvas = ChartCanvas()
        layout.addWidget(self.canvas)
        self.refresh()

    def subscribe(self) -> None:
        self.ctx.events.model_trained.connect(lambda *_: self.refresh())

    def refresh(self) -> None:
        r = self.ctx.last_train_result
        if r is None:
            self.canvas.clear("学習を実行すると表示されます")
            return
        self.canvas.barh(r.importance, xlabel="重要度", max_items=10)
