"""ダッシュボードウィジェットのレジストリ。

ウィジェットを ID + ファクトリ関数で登録する方式にしておくことで、
将来のプラグイン機構(外部モジュールが register を呼ぶだけ)への布石とする。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class WidgetSpec:
    widget_id: str
    title: str
    factory: Callable  # (AppContext) -> DashboardWidget


class WidgetRegistry:
    def __init__(self) -> None:
        self._specs: Dict[str, WidgetSpec] = {}

    def register(self, widget_id: str, title: str, factory: Callable) -> None:
        self._specs[widget_id] = WidgetSpec(widget_id, title, factory)

    def specs(self) -> List[WidgetSpec]:
        return list(self._specs.values())

    def get(self, widget_id: str) -> WidgetSpec:
        return self._specs[widget_id]
