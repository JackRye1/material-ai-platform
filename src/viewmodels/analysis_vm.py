"""特徴量解析画面の ViewModel。計算は軽いため同期実行。"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from PySide6.QtCore import QObject, Signal

from src.core.context import AppContext


class AnalysisViewModel(QObject):
    error = Signal(str)

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx

    @property
    def numeric_columns(self) -> List[str]:
        ds = self.ctx.current_dataset
        return ds.numeric_columns if ds else []

    def scatter_data(self, x: str, y: str, color_by: Optional[str]) -> Optional[pd.DataFrame]:
        ds = self.ctx.current_dataset
        if ds is None:
            return None
        try:
            return self.ctx.analysis.scatter_data(ds, x, y, color_by)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
            return None

    def correlation(self) -> Optional[pd.DataFrame]:
        ds = self.ctx.current_dataset
        if ds is None:
            return None
        try:
            return self.ctx.analysis.correlation(ds)
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
            return None
