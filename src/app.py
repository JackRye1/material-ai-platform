"""アプリケーションの初期化と起動(DI の組み立てはここに集約)。"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.config.settings import load_settings
from src.core.context import AppContext
from src.ui.main_window import MainWindow
from src.ui.widgets.chart_canvas import setup_japanese_font

BASE_DIR = Path(__file__).resolve().parents[1]


def run() -> int:
    app = QApplication(sys.argv)

    settings = load_settings(BASE_DIR)
    setup_japanese_font()

    qss = BASE_DIR / "src" / "ui" / "theme" / "dark.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))

    ctx = AppContext(settings)

    # 前回 DB に保存したデータがあれば自動復元する
    try:
        dataset = ctx.dataset_repo.load_latest()
        if dataset is not None:
            ctx.current_dataset = dataset
    except Exception:  # noqa: BLE001 - 復元失敗は起動を妨げない
        pass

    window = MainWindow(ctx)
    if ctx.current_dataset is not None:
        ctx.events.dataset_changed.emit(ctx.current_dataset)
    window.show()
    return app.exec()
