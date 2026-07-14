"""レポート生成(HTML / Excel)。Qt 非依存。

グラフは matplotlib (Agg) で描画し base64 で HTML に埋め込む。
将来の PDF 対応は生成済み HTML を QPrinter で変換する方針。
"""
from __future__ import annotations

import base64
import io
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.models.dataset import Dataset
from src.services.analysis.analysis_service import AnalysisService
from src.services.prediction.prediction_service import TrainResult

matplotlib.use("Agg")

_CSS = """
body { font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; margin: 40px;
       color: #1a2233; }
h1 { border-bottom: 3px solid #2f6fed; padding-bottom: 8px; }
h2 { color: #2f6fed; margin-top: 36px; }
table { border-collapse: collapse; margin: 12px 0; }
th, td { border: 1px solid #c6cede; padding: 6px 14px; text-align: right; }
th { background: #eef2fa; }
img { max-width: 720px; border: 1px solid #dde3ee; margin: 8px 0; }
.meta { color: #6b7690; font-size: 0.9em; }
"""


class ReportService:
    def __init__(self, report_dir: Path) -> None:
        self.report_dir = report_dir

    def export_html(
        self,
        dataset: Optional[Dataset],
        train_result: Optional[TrainResult],
        sections: List[str],
    ) -> Path:
        """sections: 'summary' | 'correlation' | 'prediction' | 'importance'"""
        parts: List[str] = [
            "<h1>材料特性 解析レポート</h1>",
            f"<p class='meta'>作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
        ]
        if dataset and "summary" in sections:
            parts.append(self._summary_section(dataset))
        if dataset and "correlation" in sections:
            parts.append(self._correlation_section(dataset))
        if train_result and "prediction" in sections:
            parts.append(self._prediction_section(train_result))
        if train_result and "importance" in sections:
            parts.append(self._importance_section(train_result))

        html = (
            f"<!DOCTYPE html><html lang='ja'><head><meta charset='utf-8'>"
            f"<title>解析レポート</title><style>{_CSS}</style></head>"
            f"<body>{''.join(parts)}</body></html>"
        )
        self.report_dir.mkdir(parents=True, exist_ok=True)
        path = self.report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path.write_text(html, encoding="utf-8")
        return path

    def export_excel(
        self, dataset: Optional[Dataset], train_result: Optional[TrainResult]
    ) -> Path:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        path = self.report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            if dataset is not None:
                dataset.df.to_excel(writer, sheet_name="データ", index=False)
            if train_result is not None:
                pd.DataFrame([train_result.metrics]).to_excel(
                    writer, sheet_name="評価指標", index=False
                )
                pd.DataFrame(
                    {"実測値": train_result.y_test, "予測値": train_result.y_pred}
                ).to_excel(writer, sheet_name="予測結果", index=False)
                pd.DataFrame(
                    train_result.importance.items(), columns=["特徴量", "重要度"]
                ).to_excel(writer, sheet_name="重要因子", index=False)
        return path

    # ---- セクション生成 ----

    @staticmethod
    def _summary_section(dataset: Dataset) -> str:
        stats = dataset.df.describe().round(3)
        return (
            f"<h2>1. データ概要</h2>"
            f"<p>データセット: {dataset.name} / {dataset.n_rows} 行 × {dataset.n_cols} 列</p>"
            f"{stats.to_html()}"
        )

    def _correlation_section(self, dataset: Dataset) -> str:
        corr = AnalysisService.correlation(dataset)
        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(corr.columns)))
        ax.set_yticklabels(corr.columns, fontsize=8)
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        return f"<h2>2. 相関マップ</h2>{self._fig_to_img(fig)}"

    def _prediction_section(self, r: TrainResult) -> str:
        m = r.metrics
        table = (
            "<table><tr><th>R²</th><th>RMSE</th><th>MAE</th></tr>"
            f"<tr><td>{m['r2']:.3f}</td><td>{m['rmse']:.3f}</td>"
            f"<td>{m['mae']:.3f}</td></tr></table>"
        )
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.scatter(r.y_test, r.y_pred, alpha=0.6, s=18)
        lims = [min(r.y_test.min(), r.y_pred.min()), max(r.y_test.max(), r.y_pred.max())]
        ax.plot(lims, lims, "r--", linewidth=1)
        ax.set_xlabel(f"実測値 ({r.target_name})")
        ax.set_ylabel("予測値")
        fig.tight_layout()
        return (
            f"<h2>3. 予測結果 ({r.model_type} / 目的変数: {r.target_name})</h2>"
            f"{table}{self._fig_to_img(fig)}"
        )

    def _importance_section(self, r: TrainResult) -> str:
        names = list(r.importance.keys())[::-1]
        values = list(r.importance.values())[::-1]
        fig, ax = plt.subplots(figsize=(6, 0.4 * len(names) + 1.2))
        ax.barh(names, values, color="#2f6fed")
        ax.set_xlabel("重要度")
        fig.tight_layout()
        return f"<h2>4. 重要因子</h2>{self._fig_to_img(fig)}"

    @staticmethod
    def _fig_to_img(fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110)
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"<img src='data:image/png;base64,{b64}'>"
