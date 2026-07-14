"""PZT 薄膜を模したダミーデータを生成する(機密情報なし・完全な架空データ)。

使い方:
    python scripts/generate_dummy_data.py [行数]
出力:
    data/dummy/pzt_dummy.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]


def generate(n: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    temp = rng.uniform(500, 650, n)          # 成膜温度 (℃)
    o2 = rng.uniform(0.05, 0.5, n)           # O2分圧 (Pa)
    rf = rng.uniform(80, 250, n)             # RFパワー (W)
    pressure = rng.uniform(0.5, 3.0, n)      # 成膜圧力 (Pa)
    anneal = rng.uniform(550, 750, n)        # アニール温度 (℃)
    la = rng.uniform(0.0, 10.0, n)           # La含有量 (mol%)
    zr_ti = rng.uniform(40, 60, n)           # Zr/Ti比 (%)
    thickness = rng.uniform(150, 500, n)     # 膜厚 (nm)

    # 残留分極 Pr: 非線形な架空の物理モデル + ノイズ
    pr = (
        30
        + 25 * np.exp(-((temp - 600) / 60) ** 2)       # 最適成膜温度 600℃
        + 12 * np.exp(-((zr_ti - 52) / 6) ** 2)        # MPB 付近で最大
        - 0.8 * la                                     # La 添加で減少
        + 0.02 * (rf - 150)
        + 5 * np.exp(-((anneal - 650) / 80) ** 2)
        - 2.0 * (o2 - 0.2) ** 2 * 10
        + rng.normal(0, 2.5, n)
    )
    ps = pr * rng.uniform(1.15, 1.35, n)                       # 飽和分極
    ec = 55 - 0.25 * (temp - 500) / 10 + 0.9 * la + rng.normal(0, 3, n)  # 抗電界

    return pd.DataFrame({
        "サンプルID": [f"S{i + 1:04d}" for i in range(n)],
        "成膜温度(℃)": temp.round(0),
        "O2分圧(Pa)": o2.round(3),
        "RFパワー(W)": rf.round(0),
        "成膜圧力(Pa)": pressure.round(2),
        "アニール温度(℃)": anneal.round(0),
        "La含有量(mol%)": la.round(2),
        "Zr/Ti比(%)": zr_ti.round(1),
        "膜厚(nm)": thickness.round(0),
        "Pr(μC/cm2)": pr.round(2),
        "Ps(μC/cm2)": ps.round(2),
        "Ec(kV/cm)": ec.round(2),
    })


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    df = generate(n)
    out = BASE_DIR / "data" / "dummy" / "pzt_dummy.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"生成完了: {out} ({len(df)} 行)")
