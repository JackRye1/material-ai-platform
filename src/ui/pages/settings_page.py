"""設定画面。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.core.context import AppContext
from src.viewmodels.settings_vm import SettingsViewModel


class SettingsPage(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.vm = SettingsViewModel(ctx)
        s = ctx.settings

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        title = QLabel("設定")
        title.setProperty("class", "pageTitle")
        root.addWidget(title)

        data_box = QGroupBox("データ設定")
        dform = QFormLayout(data_box)
        db_edit = QLineEdit(str(s.db_file))
        db_edit.setReadOnly(True)
        dform.addRow("データベース:", db_edit)
        models_edit = QLineEdit(str(s.models_path))
        models_edit.setReadOnly(True)
        dform.addRow("モデル保存先:", models_edit)
        root.addWidget(data_box)

        model_box = QGroupBox("モデル既定値")
        mform = QFormLayout(model_box)
        self.test_ratio = QDoubleSpinBox()
        self.test_ratio.setRange(0.05, 0.5)
        self.test_ratio.setSingleStep(0.05)
        self.test_ratio.setValue(s.default_test_ratio)
        mform.addRow("テストデータ割合:", self.test_ratio)
        self.n_estimators = QSpinBox()
        self.n_estimators.setRange(10, 5000)
        self.n_estimators.setValue(int(s.default_model_params.get("n_estimators", 300)))
        mform.addRow("n_estimators:", self.n_estimators)
        self.max_depth = QSpinBox()
        self.max_depth.setRange(1, 20)
        self.max_depth.setValue(int(s.default_model_params.get("max_depth", 6)))
        mform.addRow("max_depth:", self.max_depth)
        self.learning_rate = QDoubleSpinBox()
        self.learning_rate.setRange(0.001, 1.0)
        self.learning_rate.setDecimals(3)
        self.learning_rate.setSingleStep(0.01)
        self.learning_rate.setValue(float(s.default_model_params.get("learning_rate", 0.1)))
        mform.addRow("learning_rate:", self.learning_rate)
        root.addWidget(model_box)

        save_btn = QPushButton("設定を保存")
        save_btn.clicked.connect(self._save)
        root.addWidget(save_btn)
        root.addStretch()

        self.vm.saved.connect(
            lambda: QMessageBox.information(self, "保存完了", "設定を保存しました")
        )
        self.vm.error.connect(lambda msg: QMessageBox.warning(self, "エラー", msg))

    def _save(self) -> None:
        self.vm.save(
            default_test_ratio=self.test_ratio.value(),
            default_model_params={
                "n_estimators": self.n_estimators.value(),
                "max_depth": self.max_depth.value(),
                "learning_rate": self.learning_rate.value(),
            },
        )
