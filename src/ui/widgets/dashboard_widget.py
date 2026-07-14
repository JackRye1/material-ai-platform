"""ダッシュボードウィジェットの基底クラス。

新しいウィジェットは本クラスを継承し、WidgetRegistry に登録するだけで
ダッシュボードに追加される(表示切替・レイアウト保存も自動対応)。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QWidget

from src.core.context import AppContext


class DashboardWidget(QDockWidget):
    widget_id: str = ""

    def __init__(self, ctx: AppContext, title: str) -> None:
        super().__init__(title)
        self.ctx = ctx
        self.setObjectName(self.widget_id)  # saveState に必須
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        body = QWidget()
        self.setWidget(body)
        self.build_ui(body)
        self.subscribe()

    def build_ui(self, body: QWidget) -> None:
        """サブクラスで UI を構築する。"""

    def subscribe(self) -> None:
        """サブクラスでイベントバスを購読する。"""
