"use client";
// データ管理: インポート・品質チェック・カラムマッピング(列ロール設定)
import { useRef, useState } from "react";
import { api, type DataInfo } from "@/lib/api";
import { useApp } from "@/lib/store";
import DataTable from "@/components/DataTable";
import MetricTile from "@/components/MetricTile";

const ROLES = [
  { value: "id", label: "ID" },
  { value: "feature", label: "特徴量" },
  { value: "target", label: "目的変数" },
  { value: "meta", label: "メタ情報" },
  { value: "ignore", label: "無視" },
];

export default function DataPage() {
  const { passcode, data, setData } = useApp();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const run = async (fn: () => Promise<DataInfo>) => {
    setBusy(true);
    setError("");
    try {
      setData(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setBusy(false);
    }
  };

  const loadDummy = () =>
    run(() => api<DataInfo>("/api/data/dummy", { method: "POST", passcode: passcode! }));

  const upload = (file: File) =>
    run(() => {
      const form = new FormData();
      form.append("file", file);
      return api<DataInfo>("/api/data/upload", { formData: form, passcode: passcode! });
    });

  const setRole = async (column: string, role: string) => {
    if (!data) return;
    try {
      const next = await api<DataInfo>(`/api/data/${data.sid}/role`, {
        body: { column, role },
        passcode: passcode!,
      });
      setData(next, { keepResult: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "ロール変更に失敗しました");
    }
  };

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-xl font-bold">データ管理</h1>
        <div className="ml-auto flex gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
          />
          <button className="btn" onClick={() => fileRef.current?.click()} disabled={busy}>
            インポート (CSV / Excel)
          </button>
          <button className="btn btn-ghost" onClick={loadDummy} disabled={busy}>
            🧪 ダミーデータ読込 (PZT薄膜 300件)
          </button>
        </div>
      </div>

      {busy && <p className="mb-3 text-sm text-[var(--muted)]">読み込み中...</p>}
      {error && <p className="mb-3 text-sm text-[var(--bad)]">{error}</p>}

      {!data ? (
        <div className="panel p-10 text-center text-sm text-[var(--muted)]">
          CSV / Excel をインポートするか、ダミーデータを読み込んでください。
        </div>
      ) : (
        <>
          <div className="mb-4 grid grid-cols-4 gap-3">
            <MetricTile
              label="データ件数"
              value={`${data.n_rows.toLocaleString()} 行 × ${data.n_cols} 列`}
              color="var(--text)"
            />
            <MetricTile label="完全性(欠損なし率)" value={`${data.validation.completeness} %`} />
            <MetricTile
              label="外れ値候補 (3σ超)"
              value={`${data.validation.n_outliers} 件`}
              color={data.validation.n_outliers ? "var(--bad)" : "var(--good)"}
            />
            <MetricTile
              label="警告"
              value={data.validation.warnings.length ? `${data.validation.warnings.length} 件` : "なし"}
              color={data.validation.warnings.length ? "var(--bad)" : "var(--good)"}
            />
          </div>
          {data.validation.warnings.map((w) => (
            <p key={w} className="mb-2 text-xs text-[#fbbf24]">
              ⚠️ {w}
            </p>
          ))}

          <div className="flex gap-4">
            <div className="panel min-w-0 flex-1">
              <div className="panel-title">データテーブル: {data.name}(先頭100行)</div>
              <div className="h-[520px]">
                <DataTable rows={data.preview} />
              </div>
            </div>
            <div className="panel w-[300px] shrink-0">
              <div className="panel-title">カラムマッピング(列ロール)</div>
              <div className="h-[520px] overflow-auto p-3">
                {data.columns.map((c) => (
                  <div key={c.name} className="mb-2 flex items-center gap-2">
                    <span className="min-w-0 flex-1 truncate text-xs" title={c.name}>
                      {c.name}
                    </span>
                    <select
                      className="input w-[110px] text-xs"
                      value={c.role}
                      onChange={(e) => setRole(c.name, e.target.value)}
                    >
                      {ROLES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
