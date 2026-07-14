"""設定画面の ViewModel。"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.config.settings import save_settings
from src.core.context import AppContext


class SettingsViewModel(QObject):
    saved = Signal()
    error = Signal(str)

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx

    def save(self, **values) -> None:
        s = self.ctx.settings
        try:
            for key, value in values.items():
                if hasattr(s, key):
                    setattr(s, key, value)
            save_settings(s)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
            return
        self.ctx.events.settings_changed.emit(s)
        self.saved.emit()
