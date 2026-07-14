"""データセットのドメインモデル。

アプリの心臓部: DataFrame + 列ロール(ID/特徴量/目的変数/メタ/無視)。
予測・解析・将来の最適化はすべてこの Dataset を入口とする。
Qt には依存しない。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd


class ColumnRole(str, Enum):
    ID = "id"
    FEATURE = "feature"
    TARGET = "target"
    META = "meta"
    IGNORE = "ignore"

    @property
    def label(self) -> str:
        return _ROLE_LABELS[self]


_ROLE_LABELS = {
    ColumnRole.ID: "ID",
    ColumnRole.FEATURE: "特徴量",
    ColumnRole.TARGET: "目的変数",
    ColumnRole.META: "メタ情報",
    ColumnRole.IGNORE: "無視",
}


@dataclass
class Dataset:
    name: str
    df: pd.DataFrame
    roles: Dict[str, ColumnRole] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.roles:
            self.roles = self.infer_roles(self.df)

    @staticmethod
    def infer_roles(df: pd.DataFrame) -> Dict[str, ColumnRole]:
        """列名と型からロールの初期値を推定する。"""
        roles: Dict[str, ColumnRole] = {}
        id_keywords = ("id", "no", "サンプル", "試料", "sample")
        for i, col in enumerate(df.columns):
            lower = str(col).lower()
            if i == 0 and any(k in lower for k in id_keywords):
                roles[col] = ColumnRole.ID
            elif pd.api.types.is_numeric_dtype(df[col]):
                roles[col] = ColumnRole.FEATURE
            else:
                roles[col] = ColumnRole.META
        return roles

    def set_role(self, column: str, role: ColumnRole) -> None:
        if column not in self.df.columns:
            raise KeyError(f"列が存在しません: {column}")
        self.roles[column] = role

    def columns_by_role(self, role: ColumnRole) -> List[str]:
        return [c for c in self.df.columns if self.roles.get(c) == role]

    @property
    def feature_names(self) -> List[str]:
        return self.columns_by_role(ColumnRole.FEATURE)

    @property
    def target_names(self) -> List[str]:
        return self.columns_by_role(ColumnRole.TARGET)

    @property
    def numeric_columns(self) -> List[str]:
        return [
            c for c in self.df.columns
            if pd.api.types.is_numeric_dtype(self.df[c])
            and self.roles.get(c) not in (ColumnRole.ID, ColumnRole.IGNORE)
        ]

    def features(self, names: Optional[List[str]] = None) -> pd.DataFrame:
        cols = names if names is not None else self.feature_names
        return self.df[cols]

    def target(self, name: str) -> pd.Series:
        return self.df[name]

    @property
    def n_rows(self) -> int:
        return len(self.df)

    @property
    def n_cols(self) -> int:
        return len(self.df.columns)

    def roles_as_dict(self) -> Dict[str, str]:
        return {c: r.value for c, r in self.roles.items()}

    @staticmethod
    def roles_from_dict(d: Dict[str, str]) -> Dict[str, ColumnRole]:
        return {c: ColumnRole(v) for c, v in d.items()}
