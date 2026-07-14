"""CSV / Excel の読み込み。Qt 非依存。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models.dataset import Dataset

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")


class DataImporter:
    def load(self, path: str) -> Dataset:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {path}")
        ext = p.suffix.lower()
        if ext == ".csv":
            df = self._read_csv(p)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(p)
        else:
            raise ValueError(f"未対応のファイル形式です: {ext} (対応: CSV / Excel)")
        if df.empty:
            raise ValueError("ファイルにデータ行がありません")
        df.columns = [str(c).strip() for c in df.columns]
        return Dataset(name=p.stem, df=df)

    @staticmethod
    def _read_csv(p: Path) -> pd.DataFrame:
        # 日本語 CSV を想定し UTF-8 → CP932 の順で試す
        for enc in ("utf-8-sig", "cp932"):
            try:
                return pd.read_csv(p, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("文字コードを判別できません (UTF-8 / Shift-JIS のみ対応)")
