"""予測結果(実測 vs 予測)散布図ウィジェット。"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.ui.widgets.chart_canvas import ChartCanvas
from src.ui.widgets.dashboard_widget import DashboardWidget


class PredScatterWidget(DashboardWidget):
    widget_id = "pred_scatter"

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
        self.canvas.scatter(
            r.y_test, r.y_pred,
            xlabel=f"実測値 ({r.target_name})", ylabel="予測値",
            identity_line=True,
        )
