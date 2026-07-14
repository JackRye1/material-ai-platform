"""pandas DataFrame を表示する共通テーブル部品。"""
from __future__ import annotations

from typing import Optional

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QTableView


class PandasModel(QAbstractTableModel):
    def __init__(self, df: Optional[pd.DataFrame] = None) -> None:
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()

    def set_df(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        value = self._df.iat[index.row(), index.column()]
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            return f"{value:.4g}"
        return str(value)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


class DataTableView(QTableView):
    def __init__(self) -> None:
        super().__init__()
        self._model = PandasModel()
        self.setModel(self._model)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setDefaultSectionSize(110)
        self.verticalHeader().setDefaultSectionSize(26)

    def set_df(self, df: pd.DataFrame) -> None:
        self._model.set_df(df)
