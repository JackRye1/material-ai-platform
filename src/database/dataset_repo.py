"""データセットの永続化。

実データは dataset_{id} テーブルに、メタ情報(列ロール等)は datasets テーブルに保存する。
"""
from __future__ import annotations

import json
from typing import List, Optional

import pandas as pd

from src.database.connection import Database
from src.models.dataset import Dataset


class DatasetRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, dataset: Dataset) -> int:
        cur = self.db.conn.execute(
            "INSERT INTO datasets (name, table_name, n_rows, n_cols, roles) "
            "VALUES (?, '', ?, ?, ?)",
            (
                dataset.name,
                dataset.n_rows,
                dataset.n_cols,
                json.dumps(dataset.roles_as_dict(), ensure_ascii=False),
            ),
        )
        dataset_id = cur.lastrowid
        table_name = f"dataset_{dataset_id}"
        self.db.conn.execute(
            "UPDATE datasets SET table_name = ? WHERE id = ?", (table_name, dataset_id)
        )
        dataset.df.to_sql(table_name, self.db.conn, if_exists="replace", index=False)
        self.db.conn.commit()
        return dataset_id

    def load(self, dataset_id: int) -> Optional[Dataset]:
        row = self.db.conn.execute(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        if row is None:
            return None
        df = pd.read_sql(f'SELECT * FROM "{row["table_name"]}"', self.db.conn)
        roles = Dataset.roles_from_dict(json.loads(row["roles"]))
        return Dataset(name=row["name"], df=df, roles=roles)

    def load_latest(self) -> Optional[Dataset]:
        row = self.db.conn.execute(
            "SELECT id FROM datasets ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return self.load(row["id"]) if row else None

    def list_all(self) -> List[dict]:
        rows = self.db.conn.execute(
            "SELECT id, name, n_rows, n_cols, created_at FROM datasets ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
