"""Material AI Platform — Web版バックエンド (FastAPI)。

デスクトップ版と同じサービス層 (src/services) を REST API として公開する。
すべてのデータエンドポイントは X-Passcode ヘッダー(合言葉)で保護される。
起動: uvicorn api.main:app --port 8000
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import pandas as pd  # noqa: E402

from api.store import Session, store  # noqa: E402
from src.models.dataset import ColumnRole, Dataset  # noqa: E402
from src.services.analysis.analysis_service import AnalysisService  # noqa: E402
from src.services.data.importer import DataImporter  # noqa: E402
from src.services.data.validator import DataValidator  # noqa: E402
from src.services.prediction.prediction_service import PredictionService  # noqa: E402
from src.services.report.report_service import ReportService  # noqa: E402

PASSCODE = os.environ.get("APP_PASSCODE", "")
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()
]

app = FastAPI(title="Material AI Platform API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_POINTS = 2000  # グラフ描画用に返す最大点数


# ==== 認証 ====

def verify_passcode(x_passcode: str = Header(default="")) -> None:
    if not PASSCODE:
        raise HTTPException(503, "サーバー側で合言葉 (APP_PASSCODE) が未設定です")
    if x_passcode != PASSCODE:
        raise HTTPException(401, "合言葉が違います")


class AuthRequest(BaseModel):
    passcode: str


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/verify")
def auth_verify(req: AuthRequest) -> Dict[str, bool]:
    if not PASSCODE:
        raise HTTPException(503, "サーバー側で合言葉 (APP_PASSCODE) が未設定です")
    if req.passcode != PASSCODE:
        raise HTTPException(401, "合言葉が違います")
    return {"ok": True}


# ==== データ ====

def _df_records(df: pd.DataFrame, limit: int) -> List[dict]:
    # to_json 経由で NaN→null / numpy型→JSON型 を一括処理する
    return json.loads(df.head(limit).to_json(orient="records", force_ascii=False))


def _dataset_info(session: Session) -> dict:
    ds = session.dataset
    v = DataValidator().validate(ds)
    return {
        "sid": session.id,
        "name": ds.name,
        "n_rows": ds.n_rows,
        "n_cols": ds.n_cols,
        "columns": [
            {
                "name": c,
                "role": ds.roles[c].value,
                "numeric": bool(pd.api.types.is_numeric_dtype(ds.df[c])),
            }
            for c in ds.df.columns
        ],
        "numeric_columns": ds.numeric_columns,
        "preview": _df_records(ds.df, 100),
        "validation": {
            "completeness": v.completeness,
            "n_outliers": v.n_outliers,
            "n_duplicated": v.n_duplicated_rows,
            "warnings": v.warnings,
        },
        "has_result": session.result is not None,
    }


@app.post("/api/data/dummy", dependencies=[Depends(verify_passcode)])
def load_dummy() -> dict:
    ds = DataImporter().load(str(BASE_DIR / "data/dummy/pzt_dummy.csv"))
    session = store.create(ds)
    return _dataset_info(session)


@app.post("/api/data/upload", dependencies=[Depends(verify_passcode)])
async def upload(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "data.csv").suffix.lower()
    if suffix not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, f"未対応のファイル形式です: {suffix}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        ds = DataImporter().load(tmp_path)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"読み込みエラー: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    ds.name = Path(file.filename or "uploaded").stem
    session = store.create(ds)
    return _dataset_info(session)


def _get_session(sid: str) -> Session:
    session = store.get(sid)
    if session is None:
        raise HTTPException(404, "セッションが見つかりません。データを再読込してください")
    return session


@app.get("/api/data/{sid}", dependencies=[Depends(verify_passcode)])
def data_info(sid: str) -> dict:
    return _dataset_info(_get_session(sid))


class RoleRequest(BaseModel):
    column: str
    role: str


@app.post("/api/data/{sid}/role", dependencies=[Depends(verify_passcode)])
def set_role(sid: str, req: RoleRequest) -> dict:
    session = _get_session(sid)
    try:
        session.dataset.set_role(req.column, ColumnRole(req.role))
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    return _dataset_info(session)


# ==== 特徴量解析 ====

class ScatterRequest(BaseModel):
    x: str
    y: str
    color: Optional[str] = None


@app.post("/api/analysis/{sid}/scatter", dependencies=[Depends(verify_passcode)])
def scatter(sid: str, req: ScatterRequest) -> dict:
    session = _get_session(sid)
    try:
        df = AnalysisService.scatter_data(session.dataset, req.x, req.y, req.color)
    except KeyError as e:
        raise HTTPException(400, f"列が存在しません: {e}")
    if len(df) > MAX_POINTS:
        df = df.sample(MAX_POINTS, random_state=0)
    points = [
        {"x": float(r[req.x]), "y": float(r[req.y]),
         **({"c": float(r[req.color])} if req.color and req.color in df.columns
            and pd.api.types.is_numeric_dtype(df[req.color]) else {})}
        for _, r in df.iterrows()
    ]
    return {"points": points, "x": req.x, "y": req.y, "color": req.color}


@app.get("/api/analysis/{sid}/correlation", dependencies=[Depends(verify_passcode)])
def correlation(sid: str) -> dict:
    session = _get_session(sid)
    try:
        corr = AnalysisService.correlation(session.dataset)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "columns": list(corr.columns),
        "matrix": [[None if pd.isna(v) else round(float(v), 3) for v in row]
                   for row in corr.values],
    }


# ==== 特性予測 ====

class TrainRequest(BaseModel):
    target: str
    features: List[str]
    n_estimators: int = 300
    max_depth: int = 6
    learning_rate: float = 0.1
    test_ratio: float = 0.2


@app.post("/api/predict/{sid}/train", dependencies=[Depends(verify_passcode)])
def train(sid: str, req: TrainRequest) -> dict:
    session = _get_session(sid)
    service = PredictionService(registry=None, models_dir=Path(tempfile.gettempdir()))
    try:
        result = service.train(
            session.dataset,
            req.target,
            [f for f in req.features if f != req.target],
            params={
                "n_estimators": req.n_estimators,
                "max_depth": req.max_depth,
                "learning_rate": req.learning_rate,
            },
            test_ratio=req.test_ratio,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    session.result = result
    return {
        "target": result.target_name,
        "features": result.feature_names,
        "metrics": {k: round(float(v), 4) for k, v in result.metrics.items()},
        "importance": [
            {"name": k, "value": round(float(v), 4)}
            for k, v in result.importance.items()
        ],
        "scatter": [
            {"actual": round(float(a), 4), "pred": round(float(p), 4)}
            for a, p in zip(result.y_test, result.y_pred)
        ],
        "residuals": [
            {"pred": round(float(p), 4), "resid": round(float(a - p), 4)}
            for a, p in zip(result.y_test, result.y_pred)
        ],
    }


# ==== レポート ====

@app.get("/api/report/{sid}/html", dependencies=[Depends(verify_passcode)])
def report_html(sid: str) -> FileResponse:
    session = _get_session(sid)
    service = ReportService(Path(tempfile.gettempdir()) / "mai_reports")
    sections = ["summary", "correlation"] + (
        ["prediction", "importance"] if session.result else []
    )
    path = service.export_html(session.dataset, session.result, sections)
    return FileResponse(path, filename=path.name, media_type="text/html")


@app.get("/api/report/{sid}/excel", dependencies=[Depends(verify_passcode)])
def report_excel(sid: str) -> FileResponse:
    session = _get_session(sid)
    service = ReportService(Path(tempfile.gettempdir()) / "mai_reports")
    path = service.export_excel(session.dataset, session.result)
    return FileResponse(
        path, filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
