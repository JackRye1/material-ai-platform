import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 60
    x1 = rng.uniform(0, 10, n)
    x2 = rng.uniform(-5, 5, n)
    return pd.DataFrame({
        "サンプルID": [f"S{i:03d}" for i in range(n)],
        "温度": x1,
        "圧力": x2,
        "特性値": 3 * x1 - 2 * x2 + rng.normal(0, 0.1, n),
        "備考": ["-"] * n,
    })
