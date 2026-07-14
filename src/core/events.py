"""アプリ全体のイベントバス。

画面間の疎結合な連携に使う(例: データ読込 → ダッシュボード自動更新)。
新しいイベントが必要になったらシグナルを追加するだけでよい。
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    dataset_changed = Signal(object)      # Dataset
    model_trained = Signal(object)        # TrainResult
    model_registry_changed = Signal()
    settings_changed = Signal(object)     # AppSettings
