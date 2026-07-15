"use client";
// ダッシュボード: ウィジェットをドラッグ&リサイズで自由配置(react-grid-layout)
import { useCallback, useEffect, useMemo, useState } from "react";
import ReactGridLayout, {
  useContainerWidth,
  type LayoutItem,
} from "react-grid-layout";
import { api, type CorrData } from "@/lib/api";
import { useApp } from "@/lib/store";
import DataTable from "@/components/DataTable";
import {
  CorrHeatmap,
  ImportanceBar,
  PredScatter,
} from "@/components/charts";

const LAYOUT_NAMES = ["解析レイアウト", "最適化レイアウト", "実験計画レイアウト"];

const WIDGETS = [
  { id: "summary", title: "プロジェクトサマリー" },
  { id: "pred_scatter", title: "予測結果(実測 vs 予測)" },
  { id: "importance", title: "重要因子 (Feature Importance)" },
  { id: "preview", title: "データプレビュー" },
  { id: "corr", title: "相関ヒートマップ" },
];

const DEFAULT_LAYOUT: LayoutItem[] = [
  { i: "summary", x: 0, y: 0, w: 3, h: 5, minW: 2, minH: 4 },
  { i: "pred_scatter", x: 3, y: 0, w: 5, h: 8, minW: 3, minH: 5 },
  { i: "importance", x: 8, y: 0, w: 4, h: 8, minW: 3, minH: 5 },
  { i: "preview", x: 0, y: 8, w: 7, h: 7, minW: 3, minH: 4 },
  { i: "corr", x: 7, y: 8, w: 5, h: 7, minW: 3, minH: 4 },
];

export default function DashboardPage() {
  const { data, result, passcode } = useApp();
  const { width, containerRef, mounted } = useContainerWidth();
  const [layoutName, setLayoutName] = useState(LAYOUT_NAMES[0]);
  const [layout, setLayout] = useState<LayoutItem[]>(DEFAULT_LAYOUT);
  const [visible, setVisible] = useState<Record<string, boolean>>(
    Object.fromEntries(WIDGETS.map((w) => [w.id, true])),
  );
  const [corr, setCorr] = useState<CorrData | null>(null);
  const [saved, setSaved] = useState(false);

  // レイアウト切替時に localStorage から復元
  useEffect(() => {
    try {
      const rawLayout = localStorage.getItem(`mai_layout_${layoutName}`);
      const rawVisible = localStorage.getItem(`mai_visible_${layoutName}`);
      setLayout(rawLayout ? (JSON.parse(rawLayout) as LayoutItem[]) : DEFAULT_LAYOUT);
      setVisible(
        rawVisible
          ? (JSON.parse(rawVisible) as Record<string, boolean>)
          : Object.fromEntries(WIDGETS.map((w) => [w.id, true])),
      );
    } catch {
      setLayout(DEFAULT_LAYOUT);
    }
  }, [layoutName]);

  // 相関データはデータ読込時に取得
  useEffect(() => {
    if (!data || !passcode) {
      setCorr(null);
      return;
    }
    api<CorrData>(`/api/analysis/${data.sid}/correlation`, { passcode })
      .then(setCorr)
      .catch(() => setCorr(null));
  }, [data, passcode]);

  const save = useCallback(() => {
    localStorage.setItem(`mai_layout_${layoutName}`, JSON.stringify(layout));
    localStorage.setItem(`mai_visible_${layoutName}`, JSON.stringify(visible));
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }, [layoutName, layout, visible]);

  const shownWidgets = useMemo(
    () => WIDGETS.filter((w) => visible[w.id]),
    [visible],
  );
  const shownLayout = useMemo(
    () => layout.filter((l) => visible[l.i]),
    [layout, visible],
  );

  const body = (id: string) => {
    switch (id) {
      case "summary":
        return (
          <div className="space-y-2.5 p-4 text-[13px]">
            {[
              ["データセット", data ? data.name : "未読込"],
              ["データ件数", data ? `${data.n_rows.toLocaleString()} 件` : "—"],
              ["列数", data ? `${data.n_cols} 列` : "—"],
              ["予測ターゲット", result ? result.target : "—"],
              ["最新モデル R²", result ? result.metrics.r2.toFixed(3) : "—"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-[var(--muted)]">{k}</span>
                <span className="font-bold text-[#7ea6f5]">{v}</span>
              </div>
            ))}
          </div>
        );
      case "pred_scatter":
        return result ? (
          <div className="h-[calc(100%-44px)] p-2">
            <PredScatter data={result.scatter} target={result.target} />
          </div>
        ) : (
          <Empty text="特性予測ページで学習を実行すると表示されます" />
        );
      case "importance":
        return result ? (
          <div className="h-[calc(100%-44px)] p-2">
            <ImportanceBar data={result.importance} />
          </div>
        ) : (
          <Empty text="特性予測ページで学習を実行すると表示されます" />
        );
      case "preview":
        return data ? (
          <div className="h-[calc(100%-36px)]">
            <DataTable rows={data.preview} maxRows={50} />
          </div>
        ) : (
          <Empty text="データ管理ページでデータを読み込んでください" />
        );
      case "corr":
        return corr ? (
          <div className="h-[calc(100%-36px)] overflow-auto">
            <CorrHeatmap columns={corr.columns} matrix={corr.matrix} />
          </div>
        ) : (
          <Empty text="データ管理ページでデータを読み込んでください" />
        );
      default:
        return null;
    }
  };

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-xl font-bold">ダッシュボード</h1>
        <div className="ml-auto flex items-center gap-2 text-[13px]">
          <span className="text-[var(--muted)]">レイアウト:</span>
          <select
            className="input"
            value={layoutName}
            onChange={(e) => setLayoutName(e.target.value)}
          >
            {LAYOUT_NAMES.map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
          <button className="btn" onClick={save}>
            {saved ? "保存しました ✓" : "レイアウト保存"}
          </button>
          <details className="relative">
            <summary className="btn btn-ghost cursor-pointer list-none">
              表示ウィジェット ▾
            </summary>
            <div className="panel absolute right-0 z-50 mt-1 w-64 p-3">
              {WIDGETS.map((w) => (
                <label key={w.id} className="flex items-center gap-2 py-1 text-[13px]">
                  <input
                    type="checkbox"
                    checked={visible[w.id] ?? true}
                    onChange={(e) =>
                      setVisible((v) => ({ ...v, [w.id]: e.target.checked }))
                    }
                  />
                  {w.title}
                </label>
              ))}
            </div>
          </details>
        </div>
      </div>

      <div ref={containerRef}>
        {mounted && (
          <ReactGridLayout
            layout={shownLayout}
            width={width}
            gridConfig={{ cols: 12, rowHeight: 40, margin: [12, 12] }}
            dragConfig={{ enabled: true, handle: ".panel-title" }}
            onLayoutChange={(next) =>
              setLayout((prev) => [
                ...next,
                ...prev.filter((l) => !next.some((n) => n.i === l.i)),
              ])
            }
          >
            {shownWidgets.map((w) => (
              <div key={w.id} className="panel overflow-hidden">
                <div className="panel-title cursor-move">{w.title}</div>
                {body(w.id)}
              </div>
            ))}
          </ReactGridLayout>
        )}
      </div>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="flex h-[calc(100%-36px)] items-center justify-center p-4 text-center text-xs text-[var(--muted)]">
      {text}
    </div>
  );
}
