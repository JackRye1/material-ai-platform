"""特性予測画面: モデル設定 → 学習(非同期) → 評価 → モデル保存/読込。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.core.context import AppContext
from src.models.dataset import ColumnRole, Dataset
from src.services.prediction.prediction_service import TrainResult
from src.ui.widgets.chart_canvas import ChartCanvas
from src.viewmodels.prediction_vm import PredictionViewModel


class PredictionPage(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.vm = PredictionViewModel(ctx)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        title = QLabel("特性予測")
        title.setProperty("class", "pageTitle")
        root.addWidget(title)

        body = QHBoxLayout()
        body.addWidget(self._build_left_panel())
        body.addWidget(self._build_result_panel(), stretch=1)
        root.addLayout(body, stretch=1)

        # ---- VM 接続 ----
        self.vm.train_finished.connect(self._on_result)
        self.vm.model_saved.connect(lambda info: self._refresh_models())
        self.vm.error.connect(lambda msg: QMessageBox.warning(self, "エラー", msg))
        self.vm.runner.busy_changed.connect(self._on_busy)
        ctx.events.dataset_changed.connect(lambda *_: self._refresh_columns())
        self._refresh_columns()
        self._refresh_models()

    # ---- 左パネル ----

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        setting_box = QGroupBox("モデル設定")
        form = QFormLayout(setting_box)
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.vm.model_types())
        form.addRow("モデル:", self.model_combo)
        self.target_combo = QComboBox()
        form.addRow("目的変数:", self.target_combo)

        self.feature_list = QListWidget()
        self.feature_list.setMaximumHeight(160)
        form.addRow("特徴量:", self.feature_list)

        self.n_estimators = QSpinBox()
        self.n_estimators.setRange(10, 5000)
        self.n_estimators.setValue(300)
        form.addRow("n_estimators:", self.n_estimators)
        self.max_depth = QSpinBox()
        self.max_depth.setRange(1, 20)
        self.max_depth.setValue(6)
        form.addRow("max_depth:", self.max_depth)
        self.learning_rate = QDoubleSpinBox()
        self.learning_rate.setRange(0.001, 1.0)
        self.learning_rate.setSingleStep(0.01)
        self.learning_rate.setDecimals(3)
        self.learning_rate.setValue(0.1)
        form.addRow("learning_rate:", self.learning_rate)
        self.test_ratio = QDoubleSpinBox()
        self.test_ratio.setRange(0.05, 0.5)
        self.test_ratio.setSingleStep(0.05)
        self.test_ratio.setValue(self.ctx.settings.default_test_ratio)
        form.addRow("テストデータ割合:", self.test_ratio)
        layout.addWidget(setting_box)

        self.train_btn = QPushButton("学習実行")
        self.train_btn.clicked.connect(self._train)
        layout.addWidget(self.train_btn)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7d8db0;")
        layout.addWidget(self.status_label)

        model_box = QGroupBox("モデル保存 / 読込")
        mlayout = QVBoxLayout(model_box)
        save_row = QHBoxLayout()
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("モデル名を入力")
        save_row.addWidget(self.model_name_edit)
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_model)
        save_row.addWidget(save_btn)
        mlayout.addLayout(save_row)

        self.model_table = QTableWidget(0, 4)
        self.model_table.setHorizontalHeaderLabels(["名前", "目的変数", "R²", "作成日時"])
        self.model_table.verticalHeader().setVisible(False)
        self.model_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.model_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.model_table.setMaximumHeight(180)
        mlayout.addWidget(self.model_table)
        load_btn = QPushButton("選択モデルを読込・現データで評価")
        load_btn.clicked.connect(self._load_model)
        mlayout.addWidget(load_btn)
        layout.addWidget(model_box)
        layout.addStretch()
        return panel

    # ---- 右パネル(結果表示) ----

    def _build_result_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        metrics_bar = QHBoxLayout()
        self.metric_labels = {}
        for key, caption in [("r2", "R² (決定係数)"), ("rmse", "RMSE"),
                             ("mae", "MAE"), ("mape", "MAPE")]:
            box = QVBoxLayout()
            cap = QLabel(caption)
            cap.setStyleSheet("color: #7d8db0;")
            value = QLabel("—")
            value.setProperty("class", "metric")
            box.addWidget(cap)
            box.addWidget(value)
            metrics_bar.addLayout(box)
            self.metric_labels[key] = value
        metrics_bar.addStretch()
        layout.addLayout(metrics_bar)

        tabs = QTabWidget()
        self.pred_canvas = ChartCanvas()
        self.residual_canvas = ChartCanvas()
        self.importance_canvas = ChartCanvas()
        for canvas, name in [(self.pred_canvas, "実測 vs 予測"),
                             (self.residual_canvas, "残差プロット"),
                             (self.importance_canvas, "重要因子")]:
            holder = QWidget()
            h = QVBoxLayout(holder)
            h.addWidget(canvas)
            tabs.addTab(holder, name)
            canvas.clear("学習を実行すると表示されます")
        layout.addWidget(tabs, stretch=1)
        return panel

    # ---- 操作 ----

    def _train(self) -> None:
        target = self.target_combo.currentText()
        if not target:
            QMessageBox.warning(self, "エラー", "目的変数を選択してください")
            return
        features = [
            self.feature_list.item(i).text()
            for i in range(self.feature_list.count())
            if self.feature_list.item(i).checkState() == Qt.Checked
            and self.feature_list.item(i).text() != target
        ]
        params = {
            "n_estimators": self.n_estimators.value(),
            "max_depth": self.max_depth.value(),
            "learning_rate": self.learning_rate.value(),
        }
        self.vm.train(target, features, self.model_combo.currentText(),
                      params, self.test_ratio.value())

    def _save_model(self) -> None:
        name = self.model_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "エラー", "モデル名を入力してください")
            return
        self.vm.save_model(name)

    def _load_model(self) -> None:
        row = self.model_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "エラー", "モデルを選択してください")
            return
        model_id = self.model_table.item(row, 0).data(Qt.UserRole)
        self.vm.load_and_evaluate(model_id)

    # ---- 表示更新 ----

    def _on_busy(self, busy: bool) -> None:
        self.train_btn.setEnabled(not busy)
        self.status_label.setText("学習中..." if busy else "")

    def _on_result(self, r: TrainResult) -> None:
        for key, label in self.metric_labels.items():
            value = r.metrics.get(key)
            label.setText(f"{value:.3f}" if value is not None else "—")
        self.pred_canvas.scatter(
            r.y_test, r.y_pred, xlabel=f"実測値 ({r.target_name})",
            ylabel="予測値", identity_line=True,
        )
        self.residual_canvas.scatter(
            r.y_pred, r.residuals, xlabel="予測値", ylabel="残差 (実測 - 予測)",
        )
        self.importance_canvas.barh(r.importance, xlabel="重要度")

    def _refresh_columns(self) -> None:
        ds = self.ctx.current_dataset
        self.target_combo.clear()
        self.feature_list.clear()
        if ds is None:
            return
        cols = ds.numeric_columns
        self.target_combo.addItems(cols)
        targets = ds.target_names
        if targets:
            self.target_combo.setCurrentText(targets[0])
        elif cols:
            self.target_combo.setCurrentIndex(len(cols) - 1)
        default_features = set(ds.feature_names)
        for col in cols:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            checked = col in default_features and col != self.target_combo.currentText()
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.feature_list.addItem(item)

    def _refresh_models(self) -> None:
        models = self.vm.list_models()
        self.model_table.setRowCount(len(models))
        for row, info in enumerate(models):
            name_item = QTableWidgetItem(info.name)
            name_item.setData(Qt.UserRole, info.id)
            self.model_table.setItem(row, 0, name_item)
            self.model_table.setItem(row, 1, QTableWidgetItem(info.target_name))
            r2 = info.metrics.get("r2")
            self.model_table.setItem(
                row, 2, QTableWidgetItem(f"{r2:.3f}" if r2 is not None else "—")
            )
            self.model_table.setItem(row, 3, QTableWidgetItem(info.created_at))
