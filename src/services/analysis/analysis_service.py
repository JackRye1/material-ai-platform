"""特徴量解析(散布図データ・相関行列)の計算。Qt 非依存。"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from src.models.dataset import Dataset


class AnalysisService:
    @staticmethod
    def scatter_data(
        dataset: Dataset, x: str, y: str, color_by: Optional[str] = None
    ) -> pd.DataFrame:
        cols = [x, y] + ([color_by] if color_by and color_by not in (x, y) else [])
        return dataset.df[cols].dropna()

    @staticmethod
    def correlation(dataset: Dataset, columns: Optional[List[str]] = None) -> pd.DataFrame:
        cols = columns if columns else dataset.numeric_columns
        if len(cols) < 2:
            raise ValueError("相関計算には数値列が 2 列以上必要です")
        return dataset.df[cols].corr(numeric_only=True)
