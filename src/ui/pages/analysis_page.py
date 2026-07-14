"""特徴量解析画面: 散布図・相関ヒートマップ。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.core.context import AppContext
from src.ui.widgets.chart_canvas import ChartCanvas
from src.viewmodels.analysis_vm import AnalysisViewModel

NO_COLOR = "(なし)"


class AnalysisPage(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.vm = AnalysisViewModel(ctx)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        title = QLabel("特徴量解析")
        title.setProperty("class", "pageTitle")
        root.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_scatter_tab(), "散布図")
        tabs.addTab(self._build_corr_tab(), "相関ヒートマップ")
        root.addWidget(tabs, stretch=1)

        self.vm.error.connect(lambda msg: QMessageBox.warning(self, "エラー", msg))
        ctx.events.dataset_changed.connect(lambda *_: self._refresh_columns())
        self._refresh_columns()

    # ---- 散布図タブ ----

    def _build_scatter_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        self.x_combo, self.y_combo, self.color_combo = QComboBox(), QComboBox(), QComboBox()
        for label, combo in [("X軸:", self.x_combo), ("Y軸:", self.y_combo),
                             ("色分け:", self.color_combo)]:
            bar.addWidget(QLabel(label))
            combo.setMinimumWidth(150)
            bar.addWidget(combo)
        update_btn = QPushButton("グラフ更新")
        update_btn.clicked.connect(self._update_scatter)
        bar.addWidget(update_btn)
        bar.addStretch()
        layout.addLayout(bar)
        self.scatter_canvas = ChartCanvas()
        self.scatter_canvas.clear("データを読み込んで「グラフ更新」を押してください")
        layout.addWidget(self.scatter_canvas, stretch=1)
        return page

    def _update_scatter(self) -> None:
        x, y = self.x_combo.currentText(), self.y_combo.currentText()
        if not x or not y:
            return
        color = self.color_combo.currentText()
        color = None if color == NO_COLOR else color
        df = self.vm.scatter_data(x, y, color)
        if df is None or df.empty:
            self.scatter_canvas.clear("表示できるデータがありません")
            return
        color_vals = df[color].to_numpy() if color and color not in (x, y) else None
        self.scatter_canvas.scatter(
            df[x].to_numpy(), df[y].to_numpy(), xlabel=x, ylabel=y,
            color_values=color_vals, color_label=color or "",
        )

    # ---- 相関タブ ----

    def _build_corr_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        update_btn = QPushButton("相関を計算")
        update_btn.clicked.connect(self._update_corr)
        bar.addWidget(update_btn)
        bar.addStretch()
        layout.addLayout(bar)
        self.corr_canvas = ChartCanvas()
        self.corr_canvas.clear("データを読み込んで「相関を計算」を押してください")
        layout.addWidget(self.corr_canvas, stretch=1)
        return page

    def _update_corr(self) -> None:
        corr = self.vm.correlation()
        if corr is None:
            self.corr_canvas.clear("データが読み込まれていません")
            return
        self.corr_canvas.heatmap(corr)

    # ---- 共通 ----

    def _refresh_columns(self) -> None:
        cols = self.vm.numeric_columns
        for combo in (self.x_combo, self.y_combo):
            current = combo.currentText()
            combo.clear()
            combo.addItems(cols)
            if current in cols:
                combo.setCurrentText(current)
        if len(cols) >= 2 and self.y_combo.currentIndex() == 0:
            self.y_combo.setCurrentIndex(len(cols) - 1)
        self.color_combo.clear()
        self.color_combo.addItems([NO_COLOR] + cols)
