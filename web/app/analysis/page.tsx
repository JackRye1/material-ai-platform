"use client";
// 特徴量解析: 散布図・相関ヒートマップ
import { useCallback, useEffect, useState } from "react";
import { api, type CorrData, type ScatterData } from "@/lib/api";
import { useApp } from "@/lib/store";
import { CorrHeatmap, ExploreScatter } from "@/components/charts";

const NO_COLOR = "(なし)";

export default function AnalysisPage() {
  const { passcode, data } = useApp();
  const cols = data?.numeric_columns ?? [];
  const [tab, setTab] = useState<"scatter" | "corr">("scatter");
  const [x, setX] = useState("");
  const [y, setY] = useState("");
  const [color, setColor] = useState(NO_COLOR);
  const [scatter, setScatter] = useState<ScatterData | null>(null);
  const [corr, setCorr] = useState<CorrData | null>(null);
  const [error, setError] = useState("");

  // データ変更時に軸の初期値を設定
  useEffect(() => {
    if (cols.length >= 2) {
      setX((prev) => (cols.includes(prev) ? prev : cols[0]));
      setY((prev) => (cols.includes(prev) ? prev : cols[cols.length - 1]));
    }
    setScatter(null);
    setCorr(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.sid]);

  const updateScatter = useCallback(async () => {
    if (!data || !x || !y) return;
    setError("");
    try {
      setScatter(
        await api<ScatterData>(`/api/analysis/${data.sid}/scatter`, {
          body: { x, y, color: color === NO_COLOR ? null : color },
          passcode: passcode!,
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "取得に失敗しました");
    }
  }, [data, x, y, color, passcode]);

  const updateCorr = useCallback(async () => {
    if (!data) return;
    setError("");
    try {
      setCorr(await api<CorrData>(`/api/analysis/${data.sid}/correlation`, { passcode: passcode! }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "取得に失敗しました");
    }
  }, [data, passcode]);

  // 初回自動描画
  useEffect(() => {
    if (data && x && y && !scatter) void updateScatter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.sid, x, y]);
  useEffect(() => {
    if (data && tab === "corr" && !corr) void updateCorr();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, data?.sid]);

  if (!data) {
    return (
      <div>
        <h1 className="mb-4 text-xl font-bold">特徴量解析</h1>
        <div className="panel p-10 text-center text-sm text-[var(--muted)]">
          先に「データ管理」でデータを読み込んでください。
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">特徴量解析</h1>
      <div className="mb-3 flex gap-1">
        {(
          [
            ["scatter", "散布図"],
            ["corr", "相関ヒートマップ"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`rounded-t-lg px-5 py-2 text-[13px] ${
              tab === key ? "bg-[var(--accent)] text-white" : "bg-[var(--panel)] text-[var(--muted)]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && <p className="mb-3 text-sm text-[var(--bad)]">{error}</p>}

      {tab === "scatter" ? (
        <div className="panel p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2 text-[13px]">
            <span className="text-[var(--muted)]">X軸:</span>
            <select className="input" value={x} onChange={(e) => setX(e.target.value)}>
              {cols.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <span className="text-[var(--muted)]">Y軸:</span>
            <select className="input" value={y} onChange={(e) => setY(e.target.value)}>
              {cols.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <span className="text-[var(--muted)]">色分け:</span>
            <select className="input" value={color} onChange={(e) => setColor(e.target.value)}>
              {[NO_COLOR, ...cols].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <button className="btn" onClick={updateScatter}>
              グラフ更新
            </button>
          </div>
          <div className="h-[480px]">
            {scatter && (
              <ExploreScatter
                points={scatter.points}
                xLabel={scatter.x}
                yLabel={scatter.y}
                colorLabel={scatter.color}
              />
            )}
          </div>
        </div>
      ) : (
        <div className="panel p-4">
          {corr ? (
            <CorrHeatmap columns={corr.columns} matrix={corr.matrix} />
          ) : (
            <p className="p-6 text-sm text-[var(--muted)]">計算中...</p>
          )}
        </div>
      )}
    </div>
  );
}
