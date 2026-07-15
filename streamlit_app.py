"""Material AI Platform — Web版 (Streamlit Cloud 用)。

デスクトップ版と同じサービス層 (src/services, src/models) を再利用し、
画面だけを Streamlit で提供する。データはセッション中のみ保持(永続化なし)。
アクセスには合言葉 (Secrets の APP_PASSCODE) が必要。
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.models.dataset import ColumnRole, Dataset  # noqa: E402
from src.services.analysis.analysis_service import AnalysisService  # noqa: E402
from src.services.data.importer import DataImporter  # noqa: E402
from src.services.data.validator import DataValidator  # noqa: E402
from src.services.prediction.prediction_service import PredictionService  # noqa: E402
from src.services.report.report_service import ReportService  # noqa: E402

# ---- ダークテーマのグラフ配色(デスクトップ版と統一) ----
BG, AXES_BG, FG, GRID, ACCENT = "#0d1420", "#111b2c", "#c3cfe6", "#243450", "#3b82f6"

st.set_page_config(page_title="Material AI Platform", page_icon="🧪", layout="wide")


# ==== 共通ヘルパー ====

@st.cache_resource
def setup_japanese_font() -> None:
    """日本語フォントを matplotlib に設定 (Streamlit Cloud では packages.txt の Noto CJK)。"""
    from matplotlib import font_manager

    candidates = ["Noto Sans CJK JP", "Noto Sans JP", "Hiragino Sans",
                  "Yu Gothic", "Meiryo", "IPAexGothic"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def new_fig(width: float = 6.5, height: float = 4.5):
    fig, ax = plt.subplots(figsize=(width, height), facecolor=BG)
    ax.set_facecolor(AXES_BG)
    ax.tick_params(colors=FG, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, linewidth=0.5, alpha=0.5)
    return fig, ax


def scatter_fig(x, y, xlabel, ylabel, color_values=None, color_label="",
                identity_line=False):
    fig, ax = new_fig()
    if color_values is not None:
        sc = ax.scatter(x, y, c=color_values, cmap="viridis", s=22, alpha=0.85)
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label(color_label, color=FG, fontsize=8)
        cb.ax.tick_params(colors=FG, labelsize=7)
    else:
        ax.scatter(x, y, color=ACCENT, s=22, alpha=0.8)
    if identity_line and len(x) > 0:
        lims = [min(np.min(x), np.min(y)), max(np.max(x), np.max(y))]
        ax.plot(lims, lims, "--", color="#f87171", linewidth=1)
    ax.set_xlabel(xlabel, color=FG, fontsize=9)
    ax.set_ylabel(ylabel, color=FG, fontsize=9)
    fig.tight_layout()
    return fig


def barh_fig(data: dict, xlabel: str, max_items: int = 15):
    items = list(data.items())[:max_items][::-1]
    fig, ax = new_fig(6.5, 0.35 * len(items) + 1.5)
    ax.barh([k for k, _ in items], [v for _, v in items], color=ACCENT)
    ax.set_xlabel(xlabel, color=FG, fontsize=9)
    fig.tight_layout()
    return fig


def heatmap_fig(df: pd.DataFrame):
    fig, ax = new_fig(7, 6)
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
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                        color="white" if abs(v) > 0.5 else "#333")
    cb = fig.colorbar(im, ax=ax)
    cb.ax.tick_params(colors=FG, labelsize=7)
    fig.tight_layout()
    return fig


# ==== 合言葉ゲート ====

def check_passcode() -> None:
    try:
        passcode = str(st.secrets["APP_PASSCODE"])
    except (KeyError, FileNotFoundError):
        passcode = ""
    if not passcode:
        st.title("🧪 Material AI Platform")
        st.error(
            "合言葉が未設定のため利用できません。管理者は Streamlit Cloud の "
            "App settings → Secrets に `APP_PASSCODE = \"...\"` を設定してください。"
        )
        st.stop()
    if st.session_state.get("authed"):
        return
    st.title("🧪 Material AI Platform")
    st.caption("材料開発向け 特性予測・データ解析アプリ(デモ)")
    entered = st.text_input("🔒 合言葉を入力してください", type="password")
    if entered:
        if entered == passcode:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("合言葉が違います")
    st.stop()


# ==== データ読み込み ====

def load_dataset_from_upload(uploaded) -> Dataset:
    suffix = Path(uploaded.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name
    ds = DataImporter().load(tmp_path)
    ds.name = Path(uploaded.name).stem
    return ds


def page_data() -> None:
    st.header("📂 データ管理")
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded = st.file_uploader("CSV / Excel をアップロード",
                                    type=["csv", "xlsx", "xls"])
    with col2:
        st.write("")
        st.write("")
        if st.button("🧪 ダミーデータを読み込む(PZT薄膜 300件)"):
            ds = DataImporter().load(str(BASE_DIR / "data/dummy/pzt_dummy.csv"))
            st.session_state["dataset"] = ds
            st.session_state["source_id"] = "dummy"
            st.session_state.pop("train_result", None)

    if uploaded is not None and st.session_state.get("source_id") != uploaded.file_id:
        try:
            st.session_state["dataset"] = load_dataset_from_upload(uploaded)
            st.session_state["source_id"] = uploaded.file_id
            st.session_state.pop("train_result", None)
        except Exception as e:  # noqa: BLE001
            st.error(f"読み込みエラー: {e}")

    ds = st.session_state.get("dataset")
    if ds is None:
        st.info("データをアップロードするか、ダミーデータを読み込んでください。")
        return

    v = DataValidator().validate(ds)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("データ件数", f"{v.n_rows:,} 行 × {v.n_cols} 列")
    m2.metric("完全性(欠損なし率)", f"{v.completeness} %")
    m3.metric("外れ値候補 (3σ超)", f"{v.n_outliers} 件")
    m4.metric("警告", "なし" if not v.warnings else f"{len(v.warnings)} 件")
    for w in v.warnings:
        st.warning(w)

    st.subheader(f"データプレビュー: {ds.name}")
    st.dataframe(ds.df, height=380)


# ==== 特徴量解析 ====

def page_analysis() -> None:
    st.header("📊 特徴量解析")
    ds = st.session_state.get("dataset")
    if ds is None:
        st.info("先に「データ管理」でデータを読み込んでください。")
        return
    cols = ds.numeric_columns
    tab1, tab2 = st.tabs(["散布図", "相関ヒートマップ"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        x = c1.selectbox("X軸", cols, index=0)
        y = c2.selectbox("Y軸", cols, index=len(cols) - 1)
        color = c3.selectbox("色分け", ["(なし)"] + cols)
        color = None if color == "(なし)" else color
        df = AnalysisService.scatter_data(ds, x, y, color)
        color_vals = df[color].to_numpy() if color and color not in (x, y) else None
        st.pyplot(scatter_fig(df[x].to_numpy(), df[y].to_numpy(), x, y,
                              color_vals, color or ""), use_container_width=False)

    with tab2:
        try:
            st.pyplot(heatmap_fig(AnalysisService.correlation(ds)),
                      use_container_width=False)
        except ValueError as e:
            st.warning(str(e))


# ==== 特性予測 ====

def page_prediction() -> None:
    st.header("🎯 特性予測 (XGBoost)")
    ds = st.session_state.get("dataset")
    if ds is None:
        st.info("先に「データ管理」でデータを読み込んでください。")
        return

    cols = ds.numeric_columns
    targets = ds.target_names
    default_target = targets[0] if targets else cols[-1]

    with st.form("train_form"):
        c1, c2 = st.columns(2)
        target = c1.selectbox("目的変数", cols, index=cols.index(default_target))
        feature_default = [c for c in ds.feature_names if c != default_target] or \
                          [c for c in cols if c != default_target]
        features = c2.multiselect("特徴量", [c for c in cols], default=feature_default)
        p1, p2, p3, p4 = st.columns(4)
        n_estimators = p1.slider("n_estimators", 50, 1000, 300, step=50)
        max_depth = p2.slider("max_depth", 1, 15, 6)
        learning_rate = p3.select_slider(
            "learning_rate", options=[0.01, 0.03, 0.05, 0.1, 0.2, 0.3], value=0.1)
        test_ratio = p4.slider("テストデータ割合", 0.1, 0.5, 0.2, step=0.05)
        submitted = st.form_submit_button("🚀 学習実行", type="primary")

    if submitted:
        features = [f for f in features if f != target]
        if not features:
            st.error("特徴量を1つ以上選択してください(目的変数は除外されます)")
            return
        service = PredictionService(registry=None,  # Web版はDB永続化なし
                                    models_dir=Path(tempfile.gettempdir()))
        try:
            with st.spinner("学習中..."):
                result = service.train(
                    ds, target, features,
                    params={"n_estimators": n_estimators, "max_depth": max_depth,
                            "learning_rate": learning_rate},
                    test_ratio=test_ratio,
                )
            st.session_state["train_result"] = result
        except Exception as e:  # noqa: BLE001
            st.error(f"学習エラー: {e}")
            return

    r = st.session_state.get("train_result")
    if r is None:
        return

    st.subheader(f"評価結果(目的変数: {r.target_name})")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("R² (決定係数)", f"{r.metrics['r2']:.3f}")
    m2.metric("RMSE", f"{r.metrics['rmse']:.3f}")
    m3.metric("MAE", f"{r.metrics['mae']:.3f}")
    m4.metric("MAPE", f"{r.metrics.get('mape', float('nan')):.2f} %")

    tab1, tab2, tab3 = st.tabs(["実測 vs 予測", "残差プロット", "重要因子"])
    with tab1:
        st.pyplot(scatter_fig(r.y_test, r.y_pred, f"実測値 ({r.target_name})",
                              "予測値", identity_line=True),
                  use_container_width=False)
    with tab2:
        st.pyplot(scatter_fig(r.y_pred, r.residuals, "予測値", "残差 (実測 - 予測)"),
                  use_container_width=False)
    with tab3:
        st.pyplot(barh_fig(r.importance, "重要度"), use_container_width=False)

    # 成果物ダウンロード(サーバーには保存されないため)
    d1, d2 = st.columns(2)
    pred_csv = pd.DataFrame({"実測値": r.y_test, "予測値": r.y_pred}).to_csv(
        index=False).encode("utf-8-sig")
    d1.download_button("📥 予測結果CSV", pred_csv, "predictions.csv", "text/csv")
    model_path = Path(tempfile.gettempdir()) / "model_download.joblib"
    r.predictor.save(model_path)
    d2.download_button("📥 学習済みモデル (.joblib)", model_path.read_bytes(),
                       "model.joblib")


# ==== レポート ====

def page_report() -> None:
    st.header("📄 レポート")
    ds = st.session_state.get("dataset")
    r = st.session_state.get("train_result")
    if ds is None:
        st.info("先に「データ管理」でデータを読み込んでください。")
        return

    options = {"summary": "データ概要(基本統計量)", "correlation": "相関マップ"}
    if r is not None:
        options.update({"prediction": "予測結果", "importance": "重要因子"})
    else:
        st.caption("※ 予測結果・重要因子を含めるには、先に「特性予測」で学習を実行してください")
    sections = [k for k, label in options.items() if st.checkbox(label, value=True)]

    if st.button("レポート生成", type="primary"):
        service = ReportService(Path(tempfile.gettempdir()) / "reports")
        with st.spinner("生成中..."):
            html_path = service.export_html(ds, r, sections)
            xlsx_path = service.export_excel(ds, r)
        st.success("生成しました。下のボタンからダウンロードしてください。")
        c1, c2 = st.columns(2)
        c1.download_button("📥 HTML レポート", html_path.read_bytes(),
                           html_path.name, "text/html")
        c2.download_button("📥 Excel レポート", xlsx_path.read_bytes(), xlsx_path.name)


# ==== メイン ====

def main() -> None:
    setup_japanese_font()
    check_passcode()

    st.sidebar.title("🧪 Material AI Platform")
    st.sidebar.caption("材料開発向け 特性予測・データ解析(Web版デモ)")
    page = st.sidebar.radio(
        "メニュー",
        ["データ管理", "特徴量解析", "特性予測", "レポート"],
    )

    if page == "データ管理":
        page_data()
    elif page == "特徴量解析":
        page_analysis()
    elif page == "特性予測":
        page_prediction()
    elif page == "レポート":
        page_report()

    # ステータスはページ処理の後に描画する
    # (同一実行内のデータ読込・学習をサイドバーへ即時反映するため)
    st.sidebar.divider()
    ds = st.session_state.get("dataset")
    st.sidebar.write(f"**データ**: {ds.name if ds else '未読込'}")
    r = st.session_state.get("train_result")
    st.sidebar.write(f"**最新モデル R²**: {r.metrics['r2']:.3f}" if r else "**最新モデル**: なし")
    st.sidebar.divider()
    st.sidebar.caption(
        "⚠️ デモ用途: アップロードしたデータや学習結果はセッション終了時に消えます。"
        "ダミーデータのみ使用し、機密データはアップロードしないでください。"
    )


main()
