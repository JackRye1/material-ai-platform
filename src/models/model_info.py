"""学習済みモデルのメタデータ(モデルレジストリの1行分)。Qt 非依存。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ModelInfo:
    name: str
    model_type: str                     # 例: "xgboost"
    target_name: str
    feature_names: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)   # r2, rmse, mae, mape
    params: Dict[str, object] = field(default_factory=dict)
    file_path: str = ""
    dataset_name: str = ""
    created_at: str = ""
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_row(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "model_type": self.model_type,
            "target_name": self.target_name,
            "feature_names": json.dumps(self.feature_names, ensure_ascii=False),
            "metrics": json.dumps(self.metrics, ensure_ascii=False),
            "params": json.dumps(self.params, ensure_ascii=False, default=str),
            "file_path": self.file_path,
            "dataset_name": self.dataset_name,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_row(row: Dict[str, object]) -> "ModelInfo":
        return ModelInfo(
            id=row["id"],
            name=row["name"],
            model_type=row["model_type"],
            target_name=row["target_name"],
            feature_names=json.loads(row["feature_names"]),
            metrics=json.loads(row["metrics"]),
            params=json.loads(row["params"]),
            file_path=row["file_path"],
            dataset_name=row["dataset_name"],
            created_at=row["created_at"],
        )
