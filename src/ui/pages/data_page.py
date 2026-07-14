"""データ管理画面: インポート・一覧表示・列ロール設定・品質チェック。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.core.context import AppContext
from src.models.dataset import ColumnRole, Dataset
from src.services.data.validator import ValidationResult
from src.ui.widgets.data_table import DataTableView
from src.viewmodels.data_vm import DataViewModel

ROLE_ORDER = [ColumnRole.ID, ColumnRole.FEATURE, ColumnRole.TARGET,
              ColumnRole.META, ColumnRole.IGNORE]


class DataPage(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.vm = DataViewModel(ctx)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)

        # ---- ヘッダー ----
        bar = QHBoxLayout()
        title = QLabel("データ管理")
        title.setProperty("class", "pageTitle")
        bar.addWidget(title)
        bar.addStretch()
        import_btn = QPushButton("インポート (CSV / Excel)")
        import_btn.clicked.connect(self._import)
        save_btn = QPushButton("DBへ保存")
        save_btn.clicked.connect(self.vm.save_to_db)
        load_btn = QPushButton("DBから読込")
        load_btn.clicked.connect(self.vm.load_latest_from_db)
        for b in (import_btn, save_btn, load_btn):
            bar.addWidget(b)
        root.addLayout(bar)

        # ---- ステータス ----
        status = QHBoxLayout()
        self.status_labels = {}
        for key, caption in [("rows", "件数"), ("completeness", "完全性"),
                             ("outliers", "外れ値候補"), ("warnings", "警告")]:
            box = QVBoxLayout()
            cap = QLabel(caption)
            cap.setStyleSheet("color: #7d8db0;")
            value = QLabel("—")
            value.setStyleSheet("font-size: 16px; font-weight: bold;")
            box.addWidget(cap)
            box.addWidget(value)
            status.addLayout(box)
            self.status_labels[key] = value
        status.addStretch()
        root.addLayout(status)

        # ---- テーブル + ロール設定 ----
        splitter = QSplitter(Qt.Horizontal)
        self.table = DataTableView()
        splitter.addWidget(self.table)

        role_box = QGroupBox("カラムマッピング(列ロール)")
        role_layout = QVBoxLayout(role_box)
        self.role_table = QTableWidget(0, 2)
        self.role_table.setHorizontalHeaderLabels(["列名", "ロール"])
        self.role_table.horizontalHeader().setStretchLastSection(True)
        self.role_table.verticalHeader().setVisible(False)
        role_layout.addWidget(self.role_table)
        splitter.addWidget(role_box)
        splitter.setSizes([700, 300])
        root.addWidget(splitter, stretch=1)

        # ---- VM / イベントバス接続 ----
        # 他画面や起動時復元によるデータ変更も拾えるよう、イベントバスを購読する
        self._role_ds = None
        ctx.events.dataset_changed.connect(self._on_dataset_event)
        self.vm.validation_done.connect(self._on_validation)
        self.vm.error.connect(lambda msg: QMessageBox.warning(self, "エラー", msg))

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "データファイルを選択", "", "データファイル (*.csv *.xlsx *.xls)"
        )
        if path:
            self.vm.import_file(path)

    def _on_dataset_event(self, dataset: Dataset) -> None:
        self.table.set_df(dataset.df)
        # ロール変更(同一データセット)ではコンボ再構築しない
        # (シグナル発火元のコンボを破棄するとクラッシュするため)
        if dataset is not self._role_ds:
            self._role_ds = dataset
            self._build_role_table(dataset)

    def _build_role_table(self, dataset: Dataset) -> None:
        self.role_table.blockSignals(True)
        self.role_table.setRowCount(len(dataset.df.columns))
        for row, col in enumerate(dataset.df.columns):
            item = QTableWidgetItem(str(col))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.role_table.setItem(row, 0, item)

            combo = QComboBox()
            for role in ROLE_ORDER:
                combo.addItem(role.label, role.value)
            current = dataset.roles.get(col, ColumnRole.META)
            combo.setCurrentIndex(ROLE_ORDER.index(current))
            combo.currentIndexChanged.connect(
                lambda _, c=col, cb=combo: self.vm.set_role(c, cb.currentData())
            )
            self.role_table.setCellWidget(row, 1, combo)
        self.role_table.blockSignals(False)

    def _on_validation(self, v: ValidationResult) -> None:
        self.status_labels["rows"].setText(f"{v.n_rows:,} 行 × {v.n_cols} 列")
        self.status_labels["completeness"].setText(f"{v.completeness} %")
        self.status_labels["outliers"].setText(f"{v.n_outliers} 件")
        warnings = " / ".join(v.warnings) if v.warnings else "なし"
        self.status_labels["warnings"].setText(warnings)
        color = "#f87171" if v.warnings else "#4ade80"
        self.status_labels["warnings"].setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {color};"
        )
