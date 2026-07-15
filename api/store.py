"""セッション単位のインメモリデータストア。

デモ用途のため永続化しない。古いセッションは自動的に破棄する。
"""
from __future__ import annotations

import time
import uuid
from typing import Dict, Optional

from src.models.dataset import Dataset
from src.services.prediction.prediction_service import TrainResult

MAX_SESSIONS = 30
TTL_SECONDS = 2 * 60 * 60  # 2時間


class Session:
    def __init__(self, dataset: Dataset) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.dataset = dataset
        self.result: Optional[TrainResult] = None
        self.touched = time.time()

    def touch(self) -> None:
        self.touched = time.time()


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(self, dataset: Dataset) -> Session:
        self._prune()
        session = Session(dataset)
        self._sessions[session.id] = session
        return session

    def get(self, sid: str) -> Optional[Session]:
        session = self._sessions.get(sid)
        if session is not None:
            session.touch()
        return session

    def _prune(self) -> None:
        now = time.time()
        expired = [k for k, s in self._sessions.items() if now - s.touched > TTL_SECONDS]
        for k in expired:
            del self._sessions[k]
        # 上限超過時は古い順に削除
        while len(self._sessions) >= MAX_SESSIONS:
            oldest = min(self._sessions.values(), key=lambda s: s.touched)
            del self._sessions[oldest.id]


store = SessionStore()
