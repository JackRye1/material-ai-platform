"""条件最適化の抽象インターフェース(将来機能)。

MVP では実装しない。ベイズ最適化 / NSGA-II を追加するときは
BaseOptimizer を実装して register_optimizer で登録する。
学習済みモデル (BasePredictor) を目的関数として受け取る設計により、
予測モジュールと疎結合を保つ。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

import pandas as pd

_OPTIMIZER_FACTORIES: Dict[str, Callable[..., "BaseOptimizer"]] = {}


def register_optimizer(name: str, factory: Callable[..., "BaseOptimizer"]) -> None:
    _OPTIMIZER_FACTORIES[name] = factory


def available_optimizers() -> List[str]:
    return list(_OPTIMIZER_FACTORIES.keys())


@dataclass
class OptimizationSpec:
    """探索空間と目的の定義。"""
    bounds: Dict[str, Tuple[float, float]]          # 特徴量名 → (下限, 上限)
    objectives: Dict[str, str] = field(default_factory=dict)  # 目的変数名 → "maximize"/"minimize"
    n_trials: int = 100


@dataclass
class OptimizationResult:
    best_conditions: pd.DataFrame       # 提案条件(複数候補)
    predicted_values: pd.DataFrame      # 各候補の予測特性値
    history: pd.DataFrame               # 探索履歴


class BaseOptimizer(ABC):
    @abstractmethod
    def optimize(
        self,
        objective_fn: Callable[[pd.DataFrame], pd.DataFrame],
        spec: OptimizationSpec,
    ) -> OptimizationResult: ...
