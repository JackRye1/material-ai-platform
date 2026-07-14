"""ダッシュボード画面。

QDockWidget ベースの自由配置。ドラッグ&ドロップ・表示/非表示・
フローティングは Qt 標準機能。レイアウトは名前付きで保存/復元できる
(saveState のバイナリを data/layouts/<名前>.state に保存)。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMainWindow, QMenu, QMessageBox,
    QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from src.core.context import AppContext
from src.core.registry import WidgetRegistry
from src.ui.widgets.dashboard.importance_widget import ImportanceWidget
from src.ui.widgets.dashboard.pred_scatter_widget import PredScatterWidget
from src.ui.widgets.dashboard.preview_widget import PreviewWidget
from src.ui.widgets.dashboard.summary_widget import SummaryWidget

LAYOUT_NAMES = ["解析レイアウト", "最適化レイアウト", "実験計画レイアウト"]


def create_default_registry() -> WidgetRegistry:
    """標準ウィジェットの登録。プラグインはここに register を追加するだけ。"""
    reg = WidgetRegistry()
    reg.register("summary", "プロジェクトサマリー", lambda ctx: SummaryWidget(ctx, "プロジェクトサマリー"))
    reg.register("pred_scatter", "予測結果(実測 vs 予測)", lambda ctx: PredScatterWidget(ctx, "予測結果(実測 vs 予測)"))
    reg.register("importance", "重要因子", lambda ctx: ImportanceWidget(ctx, "重要因子"))
    reg.register("preview", "データプレビュー", lambda ctx: PreviewWidget(ctx, "データプレビュー"))
    return reg


class DashboardPage(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.registry = create_default_registry()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)

        # ---- ツールバー ----
        bar = QHBoxLayout()
        title = QLabel("ダッシュボード")
        title.setProperty("class", "pageTitle")
        bar.addWidget(title)
        bar.addStretch()

        bar.addWidget(QLabel("レイアウト:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(LAYOUT_NAMES)
        self.layout_combo.setMinimumWidth(170)
        bar.addWidget(self.layout_combo)

        save_btn = QPushButton("レイアウト保存")
        save_btn.clicked.connect(self._save_layout)
        bar.addWidget(save_btn)

        self.visibility_btn = QToolButton()
        self.visibility_btn.setText("表示ウィジェット ▾")
        self.visibility_btn.setPopupMode(QToolButton.InstantPopup)
        bar.addWidget(self.visibility_btn)
        root.addLayout(bar)

        # ---- ドック領域(ページ内 QMainWindow) ----
        self.inner = QMainWindow()
        self.inner.setDockNestingEnabled(True)
        placeholder = QWidget()
        placeholder.setMaximumSize(0, 0)
        self.inner.setCentralWidget(placeholder)
        root.addWidget(self.inner, stretch=1)

        self.docks = {}
        menu = QMenu(self)
        for spec in self.registry.specs():
            dock = spec.factory(ctx)
            self.docks[spec.widget_id] = dock
            menu.addAction(dock.toggleViewAction())
        self.visibility_btn.setMenu(menu)

        self._arrange_default()
        self.layout_combo.currentTextChanged.connect(self._on_layout_selected)
        self._on_layout_selected(self.layout_combo.currentText())

    # ---- 配置とレイアウト永続化 ----

    def _arrange_default(self) -> None:
        d = self.docks
        self.inner.addDockWidget(Qt.TopDockWidgetArea, d["summary"])
        self.inner.addDockWidget(Qt.TopDockWidgetArea, d["pred_scatter"])
        self.inner.splitDockWidget(d["summary"], d["pred_scatter"], Qt.Horizontal)
        self.inner.addDockWidget(Qt.BottomDockWidgetArea, d["importance"])
        self.inner.addDockWidget(Qt.BottomDockWidgetArea, d["preview"])
        self.inner.splitDockWidget(d["importance"], d["preview"], Qt.Horizontal)

    def _layout_file(self, name: str):
        return self.ctx.settings.layouts_path / f"{name}.state"

    def _save_layout(self) -> None:
        name = self.layout_combo.currentText()
        path = self._layout_file(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(self.inner.saveState()))
        QMessageBox.information(self, "保存完了", f"「{name}」を保存しました")

    def _on_layout_selected(self, name: str) -> None:
        path = self._layout_file(name)
        if path.exists():
            self.inner.restoreState(path.read_bytes())
        else:
            for dock in self.docks.values():
                dock.setVisible(True)
