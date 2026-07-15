// バックエンド (FastAPI) との通信クライアント
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Options = {
  method?: string;
  body?: unknown;
  formData?: FormData;
  passcode?: string;
};

export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.passcode) headers["X-Passcode"] = opts.passcode;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: opts.method ?? (opts.body !== undefined || opts.formData ? "POST" : "GET"),
      headers,
      body: opts.formData ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
    });
  } catch {
    throw new ApiError(0, "計算サーバーに接続できません(起動直後は30秒ほどかかる場合があります)");
  }
  if (!res.ok) {
    let detail = `エラー (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = String(data.detail);
    } catch {
      /* JSON でないエラーはそのまま */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export async function apiBlob(path: string, passcode: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "X-Passcode": passcode },
  });
  if (!res.ok) throw new ApiError(res.status, `ダウンロードに失敗しました (${res.status})`);
  return await res.blob();
}

// ==== 型定義(バックエンドのレスポンスに対応)====

export type ColumnInfo = { name: string; role: string; numeric: boolean };

export type DataInfo = {
  sid: string;
  name: string;
  n_rows: number;
  n_cols: number;
  columns: ColumnInfo[];
  numeric_columns: string[];
  preview: Record<string, unknown>[];
  validation: {
    completeness: number;
    n_outliers: number;
    n_duplicated: number;
    warnings: string[];
  };
  has_result: boolean;
};

export type TrainResult = {
  target: string;
  features: string[];
  metrics: { r2: number; rmse: number; mae: number; mape?: number };
  importance: { name: string; value: number }[];
  scatter: { actual: number; pred: number }[];
  residuals: { pred: number; resid: number }[];
};

export type ScatterData = {
  points: { x: number; y: number; c?: number }[];
  x: string;
  y: string;
  color?: string | null;
};

export type CorrData = { columns: string[]; matrix: (number | null)[][] };
