"use client";
// 特性予測: モデル設定 → XGBoost 学習 → 評価表示
import { useEffect, useState } from "react";
import { api, type TrainResult } from "@/lib/api";
import { useApp } from "@/lib/store";
import MetricTile from "@/components/MetricTile";
import { ImportanceBar, PredScatter, ResidualScatter } from "@/components/charts";

export default function PredictPage() {
  const { passcode, data, result, setResult } = useApp();
  const cols = data?.numeric_columns ?? [];
  const [target, setTarget] = useState("");
  const [features, setFeatures] = useState<Set<string>>(new Set());
  const [nEstimators, setNEstimators] = useState(300);
  const [maxDepth, setMaxDepth] = useState(6);
  const [learningRate, setLearningRate] = useState(0.1);
  const [testRatio, setTestRatio] = useState(0.2);
  const [tab, setTab] = useState<"scatter" | "resid" | "imp">("scatter");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // データ変更時に目的変数・特徴量の初期値をロールから設定
  useEffect(() => {
    if (!data) return;
    const roleTargets = data.columns.filter((c) => c.role === "target").map((c) => c.name);
    const defaultTarget = roleTargets[0] ?? cols[cols.length - 1] ?? "";
    setTarget(defaultTarget);
    const roleFeatures = data.columns
      .filter((c) => c.role === "feature" && c.numeric && c.name !== defaultTarget)
      .map((c) => c.name);
    setFeatures(new Set(roleFeatures.length ? roleFeatures : cols.filter((c) => c !== defaultTarget)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.sid]);

  const toggleFeature = (name: string) =>
    setFeatures((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });

  const train = async () => {
    if (!data) return;
    const selected = [...features].filter((f) => f !== target);
    if (!selected.length) {
      setError("特徴量を1つ以上選択してください");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await api<TrainResult>(`/api/predict/${data.sid}/train`, {
        body: {
          target,
          features: selected,
          n_estimators: nEstimators,
          max_depth: maxDepth,
          learning_rate: learningRate,
          test_ratio: testRatio,
        },
        passcode: passcode!,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "学習に失敗しました");
    } finally {
      setBusy(false);
    }
  };

  if (!data) {
    return (
      <div>
        <h1 className="mb-4 text-xl font-bold">特性予測</h1>
        <div className="panel p-10 text-center text-sm text-[var(--muted)]">
          先に「データ管理」でデータを読み込んでください。
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">特性予測 (XGBoost)</h1>
      <div className="flex gap-4">
        {/* 設定パネル */}
        <div className="w-[320px] shrink-0 space-y-4">
          <div className="panel">
            <div className="panel-title">モデル設定</div>
            <div className="space-y-3 p-4 text-[13px]">
              <label className="block">
                <span className="mb-1 block text-[var(--muted)]">目的変数</span>
                <select className="input w-full" value={target} onChange={(e) => setTarget(e.target.value)}>
                  {cols.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
              <div>
                <span className="mb-1 block text-[var(--muted)]">特徴量</span>
                <div className="max-h-[170px] overflow-auto rounded-lg border border-[var(--border)] p-2">
                  {cols
                    .filter((c) => c !== target)
                    .map((c) => (
                      <label key={c} className="flex items-center gap-2 py-0.5">
                        <input type="checkbox" checked={features.has(c)} onChange={() => toggleFeature(c)} />
                        <span className="truncate">{c}</span>
                      </label>
                    ))}
                </div>
              </div>
              <NumberField label="n_estimators" value={nEstimators} min={10} max={5000} step={50} onChange={setNEstimators} />
              <NumberField label="max_depth" value={maxDepth} min={1} max={20} step={1} onChange={setMaxDepth} />
              <NumberField label="learning_rate" value={learningRate} min={0.001} max={1} step={0.01} onChange={setLearningRate} />
              <NumberField label="テストデータ割合" value={testRatio} min={0.05} max={0.5} step={0.05} onChange={setTestRatio} />
            </div>
          </div>
          <button className="btn w-full py-2.5" onClick={train} disabled={busy}>
            {busy ? "学習中..." : "🚀 学習実行"}
          </button>
          {error && <p className="text-sm text-[var(--bad)]">{error}</p>}
        </div>

        {/* 結果パネル */}
        <div className="min-w-0 flex-1">
          {!result ? (
            <div className="panel p-10 text-center text-sm text-[var(--muted)]">
              「学習実行」を押すと、評価指標・実測vs予測・残差・重要因子が表示されます。
            </div>
          ) : (
            <>
              <div className="mb-4 grid grid-cols-4 gap-3">
                <MetricTile label="R² (決定係数)" value={result.metrics.r2.toFixed(3)} />
                <MetricTile label="RMSE" value={result.metrics.rmse.toFixed(3)} />
                <MetricTile label="MAE" value={result.metrics.mae.toFixed(3)} />
                <MetricTile
                  label="MAPE"
                  value={result.metrics.mape !== undefined ? `${result.metrics.mape.toFixed(2)} %` : "—"}
                />
              </div>
              <div className="mb-0 flex gap-1">
                {(
                  [
                    ["scatter", "実測 vs 予測"],
                    ["resid", "残差プロット"],
                    ["imp", "重要因子"],
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
              <div className="panel h-[460px] rounded-tl-none p-3">
                {tab === "scatter" && <PredScatter data={result.scatter} target={result.target} />}
                {tab === "resid" && <ResidualScatter data={result.residuals} />}
                {tab === "imp" && <ImportanceBar data={result.importance} maxItems={15} />}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-2">
      <span className="text-[var(--muted)]">{label}</span>
      <input
        type="number"
        className="input w-[110px]"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
