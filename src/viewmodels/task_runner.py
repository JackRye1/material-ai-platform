"""重い処理(学習・ファイル読込)を QThread で実行する汎用ランナー。

UI スレッドをブロックしないための共通基盤。使い方:
    runner.run(fn, on_done=..., on_error=..., args=(...))

on_done / on_error に QObject の bound method を渡すと Qt の
AutoConnection によりメインスレッドで呼ばれる。
スレッドの後始末 (_on_task_finished) も TaskRunner がメインスレッドに
住んでいるため必ずメインスレッドで実行される。
"""
from __future__ import annotations

import traceback
from typing import Callable, Dict, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _Worker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable, args: tuple, kwargs: dict) -> None:
        super().__init__()
        self._fn, self._args, self._kwargs = fn, args, kwargs

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as e:  # noqa: BLE001 - UI へエラー内容を通知する
            traceback.print_exc()
            self.failed.emit(str(e))


class TaskRunner(QObject):
    busy_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._threads: Dict[_Worker, QThread] = {}

    def run(
        self,
        fn: Callable,
        on_done: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        args: tuple = (),
        kwargs: Optional[dict] = None,
    ) -> None:
        thread = QThread()
        worker = _Worker(fn, args, kwargs or {})
        worker.moveToThread(thread)
        self._threads[worker] = thread
        self.busy_changed.emit(True)

        if on_done:
            worker.finished.connect(on_done)
        if on_error:
            worker.failed.connect(on_error)
        # bound method 接続のためメインスレッドで queued 実行される
        worker.finished.connect(self._on_task_finished)
        worker.failed.connect(self._on_task_finished)
        thread.started.connect(worker.run)
        thread.start()

    @Slot()
    def _on_task_finished(self, *_args) -> None:
        worker = self.sender()
        thread = self._threads.pop(worker, None)
        if thread is not None:
            thread.quit()
            thread.wait()
            thread.deleteLater()
            worker.deleteLater()
        if not self._threads:
            self.busy_changed.emit(False)
