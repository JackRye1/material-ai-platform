"""アプリ設定。JSON ファイルで永続化する(オフライン・可搬性重視)。Qt 非依存。"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class AppSettings:
    db_path: str = "data/material.db"
    models_dir: str = "data/models"
    layouts_dir: str = "data/layouts"
    report_dir: str = "data/reports"
    default_test_ratio: float = 0.2
    default_model_type: str = "xgboost"
    default_model_params: Dict[str, object] = field(default_factory=lambda: {
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.1,
    })
    theme: str = "dark"

    _base_dir: Path = field(default=Path("."), repr=False, compare=False)

    def resolve(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else self._base_dir / p

    @property
    def db_file(self) -> Path:
        return self.resolve(self.db_path)

    @property
    def models_path(self) -> Path:
        return self.resolve(self.models_dir)

    @property
    def layouts_path(self) -> Path:
        return self.resolve(self.layouts_dir)

    @property
    def report_path(self) -> Path:
        return self.resolve(self.report_dir)


def settings_file(base_dir: Path) -> Path:
    return base_dir / "data" / "settings.json"


def load_settings(base_dir: Path) -> AppSettings:
    path = settings_file(base_dir)
    settings = AppSettings()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for key, value in data.items():
                if hasattr(settings, key) and not key.startswith("_"):
                    setattr(settings, key, value)
        except (json.JSONDecodeError, OSError):
            pass  # 壊れた設定ファイルはデフォルトで起動する
    settings._base_dir = base_dir
    return settings


def save_settings(settings: AppSettings) -> None:
    path = settings_file(settings._base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {k: v for k, v in asdict(settings).items() if not k.startswith("_")}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
