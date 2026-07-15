# Material AI Platform (MVP)

材料開発における特性予測・データ解析を支援するアプリ。
ダミーデータのみを使用し、機密情報は一切含まない。

- **デスクトップ版** (PySide6): フル機能。ダッシュボード・レイアウト保存・モデル管理
- **Web版** (Next.js + FastAPI): ブラウザ向け本格版。デスクトップ版と同じダークUI・
  ウィジェットのドラッグ配置・レイアウト保存に対応(フロント=Vercel / API=Render)
- **簡易Web版** (Streamlit): 最小構成のデモ(Streamlit Cloud 用、`streamlit_app.py`)

## デスクトップ版の起動

```bash
# 初回のみ
python -m venv .venv
.venv/bin/pip install -r requirements-desktop.txt  # Windows: .venv\Scripts\pip
python scripts/generate_dummy_data.py              # ダミーデータ生成

# 起動
.venv/bin/python main.py                           # Windows: .venv\Scripts\python main.py
```

## Web版の起動(ローカル)

```bash
# バックエンド (FastAPI)
.venv/bin/pip install -r requirements-api.txt
APP_PASSCODE=demo1234 .venv/bin/uvicorn api.main:app --port 8000

# フロントエンド (Next.js) — 別ターミナルで
cd web && npm install && npm run dev
# → http://localhost:3000 を開き、合言葉 demo1234 で入室
```

## Web版のデプロイ

| 部分 | サービス | 設定 |
|---|---|---|
| バックエンド | Render (無料) | Blueprint で `render.yaml` を読み込み。`APP_PASSCODE` に合言葉を設定 |
| フロントエンド | Vercel | Root Directory=`web`、環境変数 `NEXT_PUBLIC_API_URL`=Render の URL |

- アクセスには合言葉が必要(バックエンドの `APP_PASSCODE` で検証)
- データはセッション中のみ保持(2時間で自動破棄)。デモ用途でありデータ蓄積はしない
- Render 無料プランはスリープするため、初回アクセスに30秒〜1分かかる場合あり

(旧・簡易Web版: `streamlit_app.py`。Streamlit Cloud に Secrets `APP_PASSCODE` を設定して利用)

- 推奨: Python 3.11+(3.9 でも動作)
- **macOS(開発時)のみ**: XGBoost に OpenMP が必要。Homebrew があれば
  `brew install libomp`。無い場合は sklearn 同梱の libomp を参照させる:
  ```bash
  install_name_tool -add_rpath "$(pwd)/.venv/lib/python3.9/site-packages/sklearn/.dylibs" \
      .venv/lib/python3.9/site-packages/xgboost/lib/libxgboost.dylib
  codesign -f -s - .venv/lib/python3.9/site-packages/xgboost/lib/libxgboost.dylib
  ```
  Windows では不要(VC++ 再頒布可能パッケージに含まれる)。

## テスト

```bash
.venv/bin/python -m pytest tests/
```

## 使い方(最短フロー)

1. **データ管理** → 「インポート」で `data/dummy/pzt_dummy.csv` を読込
2. カラムマッピングで `Pr(μC/cm2)` を **目的変数** に設定(`Ps`/`Ec` は無視推奨)
3. **特徴量解析** → 散布図・相関ヒートマップで確認
4. **特性予測** → 「学習実行」→ R²/RMSE/MAE と重要因子を確認 → モデル保存
5. **レポート** → HTML / Excel 出力
6. **ダッシュボード** → ウィジェットをドラッグ配置し「レイアウト保存」

## アーキテクチャ

依存方向は UI → ViewModel → Service → Data の一方通行。
Service 層以下は Qt 非依存で、UI なしで単体テストできる。

```
src/
├── ui/            画面(ロジックなし)
│   ├── pages/     6画面: ダッシュボード/データ管理/特徴量解析/特性予測/レポート/設定
│   ├── widgets/   共通部品 + dashboard/(ダッシュボードウィジェット)
│   └── theme/     ダークテーマ QSS
├── viewmodels/    画面状態・UI⇔Service 仲介(task_runner = QThread 非同期実行)
├── services/
│   ├── data/          CSV/Excel 取込・品質チェック
│   ├── prediction/    BasePredictor(抽象I/F)+ XGBoost 実装・評価・学習管理
│   ├── optimization/  BaseOptimizer(将来機能のI/Fのみ)
│   ├── analysis/      散布図・相関
│   └── report/        HTML / Excel 生成
├── models/        ドメインモデル(Dataset=DataFrame+列ロール, ModelInfo)
├── database/      SQLite 接続・マイグレーション・リポジトリ
├── config/        JSON 設定
└── core/          AppContext(DI)・EventBus・WidgetRegistry
```

## 拡張ポイント(将来機能の追加方法)

| 追加したいもの | やること |
|---|---|
| 予測モデル(RF/GP/LightGBM) | `BasePredictor` を実装し `register_predictor()` を呼ぶ。UI変更不要 |
| 最適化(ベイズ/NSGA-II) | `BaseOptimizer` を実装し登録。学習済み Predictor を目的関数に使う |
| ダッシュボードウィジェット | `DashboardWidget` を継承し `WidgetRegistry.register()`(dashboard_page.py) |
| 画面 | `ui/pages/` にページ追加 → `main_window.py` の pages リストに1行追加 |
| DBスキーマ変更 | `database/connection.py` の `MIGRATIONS` に SQL を追記 |
| PDF レポート | 生成済み HTML を QPrinter で変換 |

## Windows 配布(将来)

PyInstaller を想定。xgboost / matplotlib は hidden-import の指定が必要になる場合あり。
