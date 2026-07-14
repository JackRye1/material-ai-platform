"""SQLite 接続とスキーマ管理。

マイグレーションは番号付き SQL のリストで管理し、schema_version テーブルで
適用済みバージョンを追跡する。スキーマ変更時は MIGRATIONS に追記するだけでよい。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

MIGRATIONS: List[str] = [
    # v1: 初期スキーマ
    """
    CREATE TABLE IF NOT EXISTS datasets (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        table_name  TEXT NOT NULL,
        n_rows      INTEGER NOT NULL,
        n_cols      INTEGER NOT NULL,
        roles       TEXT NOT NULL,
        created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    CREATE TABLE IF NOT EXISTS models (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        model_type    TEXT NOT NULL,
        target_name   TEXT NOT NULL,
        feature_names TEXT NOT NULL,
        metrics       TEXT NOT NULL,
        params        TEXT NOT NULL,
        file_path     TEXT NOT NULL,
        dataset_name  TEXT NOT NULL DEFAULT '',
        created_at    TEXT NOT NULL
    );
    """,
]


class Database:
    def __init__(self, db_file: Path) -> None:
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self.db_file = db_file
        # 学習・読込はワーカースレッドで走るため check_same_thread を無効化する。
        # アクセスは単発の読み書きのみで、書き込みは実質メインスレッドに限られる。
        self.conn = sqlite3.connect(str(db_file), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
        )
        row = cur.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
        current = row["v"] or 0
        for version, sql in enumerate(MIGRATIONS, start=1):
            if version > current:
                cur.executescript(sql)
                cur.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
