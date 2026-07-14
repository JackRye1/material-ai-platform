"""matplotlib をダークテーマで埋め込む共通チャート部品。

チャート描画をここに集約しておくことで、将来 pyqtgraph 等へ
差し替える場合もこのクラスの置き換えだけで済む。
"""
from __future__ import annotations

from typing import Dict, Optional

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

BG = "#0f1828"
AXES_BG = "#111b2c"
FG = "#c3cfe6"
GRID = "#243450"
ACCENT = "#3b82f6"


def setup_japanese_font() -> None:
    """環境にある日本語フォントを matplotlib に設定する(Win/mac 両対応)。"""
    from matplotlib import font_manager

    candidates = [
        "Hiragino Sans", "Hiragino Kaku Gothic ProN",   # macOS
        "Yu Gothic", "Meiryo", "MS Gothic",             # Windows
        "Noto Sans CJK JP", "IPAexGothic",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, width: float = 5.0, height: float = 4.0) -> None:
        self.fig = Figure(figsize=(width, height), facecolor=BG, tight_layout=True)
        super().__init__(self.fig)

    def _new_axes(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=AXES_BG)
        ax.tick_params(colors=FG, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.grid(True, color=GRID, linewidth=0.5, alpha=0.5)
        return ax

    def clear(self, message: str = "") -> None:
        self.fig.clear()
        if message:
            self.fig.text(0.5, 0.5, message, ha="center", va="center", color=FG)
        self.draw_idle()

    def scatter(
        self,
        x: np.ndarray,
        y: np.ndarray,
        xlabel: str,
        ylabel: str,
        color_values: Optional[np.ndarray] = None,
        color_label: str = "",
        identity_line: bool = False,
    ) -> None:
        ax = self._new_axes()
        if color_values is not None:
            sc = ax.scatter(x, y, c=color_values, cmap="viridis", s=22, alpha=0.85)
            cb = self.fig.colorbar(sc, ax=ax)
            cb.set_label(color_label, color=FG, fontsize=8)
            cb.ax.tick_params(colors=FG, labelsize=7)
        else:
            ax.scatter(x, y, color=ACCENT, s=22, alpha=0.8)
        if identity_line and len(x) > 0:
            lims = [min(np.min(x), np.min(y)), max(np.max(x), np.max(y))]
            ax.plot(lims, lims, "--", color="#f87171", linewidth=1)
        ax.set_xlabel(xlabel, color=FG, fontsize=9)
        ax.set_ylabel(ylabel, color=FG, fontsize=9)
        self.draw_idle()

    def barh(self, data: Dict[str, float], xlabel: str, max_items: int = 15) -> None:
        items = list(data.items())[:max_items][::-1]
        ax = self._new_axes()
        names = [k for k, _ in items]
        values = [v for _, v in items]
        ax.barh(names, values, color=ACCENT)
        ax.set_xlabel(xlabel, color=FG, fontsize=9)
        self.draw_idle()

    def heatmap(self, df: pd.DataFrame) -> None:
        ax = self._new_axes()
        ax.grid(False)
        im = ax.imshow(df.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(df.columns)))
        ax.set_xticklabels(df.columns, rotation=45, ha="right", fontsize=7, color=FG)
        ax.set_yticks(range(len(df.index)))
        ax.set_yticklabels(df.index, fontsize=7, color=FG)
        if len(df.columns) <= 12:
            for i in range(len(df.index)):
                for j in range(len(df.columns)):
                    v = df.values[i, j]
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                            fontsize=6, color="white" if abs(v) > 0.5 else "#333")
        cb = self.fig.colorbar(im, ax=ax)
        cb.ax.tick_params(colors=FG, labelsize=7)
        self.draw_idle()
