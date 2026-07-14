"""メインウィンドウ: サイドバー + ページ切替。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget,
    QWidget,
)

from src.core.context import AppContext
from src.ui.pages.analysis_page import AnalysisPage
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.data_page import DataPage
from src.ui.pages.prediction_page import PredictionPage
from src.ui.pages.report_page import ReportPage
from src.ui.pages.settings_page import SettingsPage

APP_NAME = "Material AI Platform"
VERSION = "0.1.0 (MVP)"


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(f"{APP_NAME}  v{VERSION}")
        self.resize(1360, 860)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- サイドバー ----
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(190)
        pages = [
            ("ダッシュボード", DashboardPage(ctx)),
            ("データ管理", DataPage(ctx)),
            ("特徴量解析", AnalysisPage(ctx)),
            ("特性予測", PredictionPage(ctx)),
            ("レポート", ReportPage(ctx)),
            ("設定", SettingsPage(ctx)),
        ]
        self.stack = QStackedWidget()
        for name, page in pages:
            self.sidebar.addItem(QListWidgetItem(name))
            self.stack.addWidget(page)

        # 将来機能はグレーアウト表示のみ(設計上の位置を明示)
        for future_name in ("最適化(将来)", "実験計画(将来)"):
            item = QListWidgetItem(future_name)
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.sidebar.addItem(item)

        self.sidebar.currentRowChanged.connect(self._on_page_changed)
        self.sidebar.setCurrentRow(0)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, stretch=1)
        self.setCentralWidget(central)

        self.statusBar().showMessage(
            f"データベース: {ctx.settings.db_file}   |   バージョン: {VERSION}"
        )

    def _on_page_changed(self, row: int) -> None:
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)

    def closeEvent(self, event) -> None:
        self.ctx.shutdown()
        super().closeEvent(event)
