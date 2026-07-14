"""プロジェクトサマリーウィジェット。"""
from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from src.ui.widgets.dashboard_widget import DashboardWidget


class SummaryWidget(DashboardWidget):
    widget_id = "summary"

    def build_ui(self, body: QWidget) -> None:
        layout = QGridLayout(body)
        layout.setContentsMargins(14, 10, 14, 10)
        self._values = {}
        rows = [
            ("dataset", "データセット"),
            ("rows", "データ件数"),
            ("models", "保存モデル数"),
            ("target", "予測ターゲット"),
            ("r2", "最新モデル R²"),
        ]
        for i, (key, label) in enumerate(rows):
            layout.addWidget(QLabel(label), i, 0)
            value = QLabel("—")
            value.setStyleSheet("font-weight: bold; color: #7ea6f5;")
            layout.addWidget(value, i, 1)
            self._values[key] = value
        layout.setRowStretch(len(rows), 1)
        self.refresh()

    def subscribe(self) -> None:
        self.ctx.events.dataset_changed.connect(lambda *_: self.refresh())
        self.ctx.events.model_trained.connect(lambda *_: self.refresh())
        self.ctx.events.model_registry_changed.connect(lambda *_: self.refresh())

    def refresh(self) -> None:
        ds = self.ctx.current_dataset
        result = self.ctx.last_train_result
        self._values["dataset"].setText(ds.name if ds else "未読込")
        self._values["rows"].setText(f"{ds.n_rows:,} 件" if ds else "—")
        self._values["models"].setText(str(len(self.ctx.model_registry.list_all())))
        self._values["target"].setText(result.target_name if result else "—")
        self._values["r2"].setText(f"{result.metrics['r2']:.3f}" if result else "—")
