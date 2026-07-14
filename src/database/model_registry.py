"""学習済みモデルのメタデータを管理するレジストリ。"""
from __future__ import annotations

from typing import List, Optional

from src.database.connection import Database
from src.models.model_info import ModelInfo


class ModelRegistry:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, info: ModelInfo) -> int:
        row = info.to_row()
        cols = ", ".join(row.keys())
        placeholders = ", ".join("?" for _ in row)
        cur = self.db.conn.execute(
            f"INSERT INTO models ({cols}) VALUES ({placeholders})",
            list(row.values()),
        )
        self.db.conn.commit()
        info.id = cur.lastrowid
        return info.id

    def get(self, model_id: int) -> Optional[ModelInfo]:
        row = self.db.conn.execute(
            "SELECT * FROM models WHERE id = ?", (model_id,)
        ).fetchone()
        return ModelInfo.from_row(dict(row)) if row else None

    def list_all(self) -> List[ModelInfo]:
        rows = self.db.conn.execute(
            "SELECT * FROM models ORDER BY created_at DESC"
        ).fetchall()
        return [ModelInfo.from_row(dict(r)) for r in rows]

    def delete(self, model_id: int) -> None:
        self.db.conn.execute("DELETE FROM models WHERE id = ?", (model_id,))
        self.db.conn.commit()
