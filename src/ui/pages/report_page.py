"""レポート画面: HTML / Excel 出力。"""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from src.core.context import AppContext
from src.viewmodels.report_vm import ReportViewModel

SECTIONS = [
    ("summary", "データ概要(基本統計量)"),
    ("correlation", "相関マップ"),
    ("prediction", "予測結果(評価指標・実測vs予測)"),
    ("importance", "重要因子"),
]


class ReportPage(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.vm = ReportViewModel(ctx)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        title = QLabel("レポート")
        title.setProperty("class", "pageTitle")
        root.addWidget(title)

        section_box = QGroupBox("レポートに含める内容")
        slayout = QVBoxLayout(section_box)
        self.checks = {}
        for key, caption in SECTIONS:
            cb = QCheckBox(caption)
            cb.setChecked(True)
            slayout.addWidget(cb)
            self.checks[key] = cb
        root.addWidget(section_box)

        btn_bar = QHBoxLayout()
        html_btn = QPushButton("HTML 出力")
        html_btn.clicked.connect(self._export_html)
        excel_btn = QPushButton("Excel 出力")
        excel_btn.clicked.connect(self.vm.export_excel)
        btn_bar.addWidget(html_btn)
        btn_bar.addWidget(excel_btn)
        btn_bar.addStretch()
        root.addLayout(btn_bar)

        result_bar = QHBoxLayout()
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("color: #4ade80;")
        result_bar.addWidget(self.result_label)
        self.open_btn = QPushButton("開く")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self._open_last)
        result_bar.addWidget(self.open_btn)
        result_bar.addStretch()
        root.addLayout(result_bar)
        root.addStretch()

        self._last_path = ""
        self.vm.exported.connect(self._on_exported)
        self.vm.error.connect(lambda msg: QMessageBox.warning(self, "エラー", msg))

    def _export_html(self) -> None:
        sections = [k for k, cb in self.checks.items() if cb.isChecked()]
        if not sections:
            QMessageBox.warning(self, "エラー", "出力する内容を選択してください")
            return
        if self.ctx.current_dataset is None:
            QMessageBox.warning(self, "エラー", "データが読み込まれていません")
            return
        self.vm.export_html(sections)

    def _on_exported(self, path: str) -> None:
        self._last_path = path
        self.result_label.setText(f"出力しました: {path}")
        self.open_btn.setVisible(True)

    def _open_last(self) -> None:
        if self._last_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_path))
