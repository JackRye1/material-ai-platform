"""データ品質チェック(欠損・重複・外れ値の概況)。Qt 非依存。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd

from src.models.dataset import Dataset


@dataclass
class ValidationResult:
    n_rows: int = 0
    n_cols: int = 0
    missing_by_column: Dict[str, int] = field(default_factory=dict)
    n_duplicated_rows: int = 0
    outlier_by_column: Dict[str, int] = field(default_factory=dict)  # 3σ超え
    warnings: List[str] = field(default_factory=list)

    @property
    def completeness(self) -> float:
        """欠損なしセルの割合 (%)"""
        total = self.n_rows * self.n_cols
        if total == 0:
            return 0.0
        missing = sum(self.missing_by_column.values())
        return round((1 - missing / total) * 100, 1)

    @property
    def n_outliers(self) -> int:
        return sum(self.outlier_by_column.values())


class DataValidator:
    def validate(self, dataset: Dataset) -> ValidationResult:
        df = dataset.df
        result = ValidationResult(n_rows=len(df), n_cols=len(df.columns))

        missing = df.isna().sum()
        result.missing_by_column = {c: int(n) for c, n in missing.items() if n > 0}

        result.n_duplicated_rows = int(df.duplicated().sum())

        for col in dataset.numeric_columns:
            s = df[col].dropna()
            if len(s) < 3 or s.std() == 0:
                continue
            z = np.abs((s - s.mean()) / s.std())
            n_out = int((z > 3).sum())
            if n_out > 0:
                result.outlier_by_column[col] = n_out

        if result.missing_by_column:
            result.warnings.append(
                f"欠損値あり: {len(result.missing_by_column)} 列 "
                f"(計 {sum(result.missing_by_column.values())} 件)"
            )
        if result.n_duplicated_rows:
            result.warnings.append(f"重複行: {result.n_duplicated_rows} 件")
        if result.outlier_by_column:
            result.warnings.append(f"外れ値候補 (3σ超): 計 {result.n_outliers} 件")
        return result
