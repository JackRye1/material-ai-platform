"use client";
// レポート: HTML / Excel のダウンロード
import { useState } from "react";
import { apiBlob } from "@/lib/api";
import { useApp } from "@/lib/store";

export default function ReportPage() {
  const { passcode, data, result } = useApp();
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const download = async (kind: "html" | "excel") => {
    if (!data) return;
    setBusy(kind);
    setError("");
    try {
      const blob = await apiBlob(`/api/report/${data.sid}/${kind}`, passcode!);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report_${data.name}.${kind === "html" ? "html" : "xlsx"}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "出力に失敗しました");
    } finally {
      setBusy("");
    }
  };

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">レポート</h1>
      {!data ? (
        <div className="panel p-10 text-center text-sm text-[var(--muted)]">
          先に「データ管理」でデータを読み込んでください。
        </div>
      ) : (
        <div className="panel max-w-[640px] p-6">
          <p className="mb-1 text-sm">
            データ: <b>{data.name}</b>({data.n_rows.toLocaleString()} 行)
          </p>
          <p className="mb-5 text-sm text-[var(--muted)]">
            {result
              ? `学習済みモデル(目的変数: ${result.target})の評価結果・重要因子を含むレポートを出力します。`
              : "※ 現在は学習結果がないため、データ概要と相関マップのみのレポートになります。予測結果を含めるには先に「特性予測」で学習を実行してください。"}
          </p>
          <div className="flex gap-3">
            <button className="btn" onClick={() => download("html")} disabled={!!busy}>
              {busy === "html" ? "生成中..." : "📥 HTML レポート"}
            </button>
            <button className="btn" onClick={() => download("excel")} disabled={!!busy}>
              {busy === "excel" ? "生成中..." : "📥 Excel レポート"}
            </button>
          </div>
          {error && <p className="mt-4 text-sm text-[var(--bad)]">{error}</p>}
        </div>
      )}
    </div>
  );
}
