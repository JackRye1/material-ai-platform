"use client";
// グラフ部品(recharts ベース、ダークテーマ)
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const GRID = "#243450";
const FG = "#9fb3d9";
const ACCENT = "#3b82f6";

const axisProps = {
  stroke: GRID,
  tick: { fill: FG, fontSize: 11 },
  tickLine: { stroke: GRID },
};

const tooltipStyle = {
  contentStyle: {
    background: "#16223a",
    border: "1px solid #2a3a55",
    borderRadius: 8,
    fontSize: 12,
    color: "#d6deeb",
  },
};

// viridis 風の連続カラースケール
function colorScale(v: number, min: number, max: number): string {
  const t = max > min ? (v - min) / (max - min) : 0.5;
  const stops = [
    [68, 1, 84],
    [59, 82, 139],
    [33, 145, 140],
    [94, 201, 98],
    [253, 231, 37],
  ];
  const pos = t * (stops.length - 1);
  const i = Math.min(Math.floor(pos), stops.length - 2);
  const f = pos - i;
  const c = stops[i].map((a, k) => Math.round(a + (stops[i + 1][k] - a) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

export function ExploreScatter({
  points,
  xLabel,
  yLabel,
  colorLabel,
}: {
  points: { x: number; y: number; c?: number }[];
  xLabel: string;
  yLabel: string;
  colorLabel?: string | null;
}) {
  const hasColor = colorLabel && points.some((p) => p.c !== undefined);
  const cVals = points.map((p) => p.c ?? 0);
  const cMin = Math.min(...cVals);
  const cMax = Math.max(...cVals);
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 10, right: 20, bottom: 18, left: 10 }}>
        <CartesianGrid stroke={GRID} strokeWidth={0.5} />
        <XAxis
          dataKey="x"
          type="number"
          domain={["auto", "auto"]}
          name={xLabel}
          label={{ value: xLabel, position: "insideBottom", offset: -12, fill: FG, fontSize: 12 }}
          {...axisProps}
        />
        <YAxis
          dataKey="y"
          type="number"
          domain={["auto", "auto"]}
          name={yLabel}
          label={{ value: yLabel, angle: -90, position: "insideLeft", fill: FG, fontSize: 12 }}
          {...axisProps}
        />
        <Tooltip {...tooltipStyle} cursor={{ strokeDasharray: "3 3", stroke: GRID }} />
        <Scatter data={points} isAnimationActive={false} fill={ACCENT} fillOpacity={0.8}>
          {hasColor &&
            points.map((p, i) => (
              <Cell key={i} fill={colorScale(p.c ?? 0, cMin, cMax)} />
            ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function PredScatter({
  data,
  target,
}: {
  data: { actual: number; pred: number }[];
  target: string;
}) {
  const all = data.flatMap((d) => [d.actual, d.pred]);
  const min = Math.min(...all);
  const max = Math.max(...all);
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 10, right: 20, bottom: 18, left: 10 }}>
        <CartesianGrid stroke={GRID} strokeWidth={0.5} />
        <XAxis
          dataKey="actual"
          type="number"
          domain={[min, max]}
          label={{ value: `実測値 (${target})`, position: "insideBottom", offset: -12, fill: FG, fontSize: 12 }}
          {...axisProps}
        />
        <YAxis
          dataKey="pred"
          type="number"
          domain={[min, max]}
          label={{ value: "予測値", angle: -90, position: "insideLeft", fill: FG, fontSize: 12 }}
          {...axisProps}
        />
        <Tooltip {...tooltipStyle} cursor={{ strokeDasharray: "3 3", stroke: GRID }} />
        <ReferenceLine
          segment={[{ x: min, y: min }, { x: max, y: max }]}
          stroke="#f87171"
          strokeDasharray="5 4"
        />
        <Scatter data={data} fill={ACCENT} fillOpacity={0.75} isAnimationActive={false} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function ResidualScatter({ data }: { data: { pred: number; resid: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 10, right: 20, bottom: 18, left: 10 }}>
        <CartesianGrid stroke={GRID} strokeWidth={0.5} />
        <XAxis
          dataKey="pred"
          type="number"
          domain={["auto", "auto"]}
          label={{ value: "予測値", position: "insideBottom", offset: -12, fill: FG, fontSize: 12 }}
          {...axisProps}
        />
        <YAxis
          dataKey="resid"
          type="number"
          domain={["auto", "auto"]}
          label={{ value: "残差", angle: -90, position: "insideLeft", fill: FG, fontSize: 12 }}
          {...axisProps}
        />
        <Tooltip {...tooltipStyle} cursor={{ strokeDasharray: "3 3", stroke: GRID }} />
        <ReferenceLine y={0} stroke="#f87171" strokeDasharray="5 4" />
        <Scatter data={data} fill={ACCENT} fillOpacity={0.75} isAnimationActive={false} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function ImportanceBar({
  data,
  maxItems = 10,
}: {
  data: { name: string; value: number }[];
  maxItems?: number;
}) {
  const items = data.slice(0, maxItems);
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={items} layout="vertical" margin={{ top: 5, right: 25, bottom: 5, left: 30 }}>
        <CartesianGrid stroke={GRID} strokeWidth={0.5} horizontal={false} />
        <XAxis type="number" {...axisProps} />
        <YAxis dataKey="name" type="category" width={110} {...axisProps} />
        <Tooltip {...tooltipStyle} cursor={{ fill: "#16223a" }} />
        <Bar dataKey="value" name="重要度" fill={ACCENT} isAnimationActive={false} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// 相関ヒートマップ(CSS グリッドで描画)
function corrColor(v: number | null): string {
  if (v === null) return "#1a2438";
  const t = (v + 1) / 2; // 0(=-1 青) → 1(=+1 赤)
  const r = Math.round(30 + t * 209);
  const b = Math.round(239 - t * 180);
  const g = Math.round(60 + (1 - Math.abs(v)) * 80);
  return `rgb(${r},${g},${b})`;
}

export function CorrHeatmap({
  columns,
  matrix,
}: {
  columns: string[];
  matrix: (number | null)[][];
}) {
  return (
    <div className="overflow-auto p-2">
      <table className="border-collapse text-[10px]">
        <thead>
          <tr>
            <th />
            {columns.map((c) => (
              <th
                key={c}
                className="max-w-[70px] overflow-hidden p-1 align-bottom font-normal text-[var(--muted)]"
                title={c}
              >
                <div className="truncate [writing-mode:vertical-rl] mx-auto h-[72px]">{c}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <td className="max-w-[110px] truncate pr-2 text-right text-[var(--muted)]" title={columns[i]}>
                {columns[i]}
              </td>
              {row.map((v, j) => (
                <td
                  key={j}
                  className="h-[30px] w-[34px] text-center"
                  style={{
                    background: corrColor(v),
                    color: v !== null && Math.abs(v) > 0.5 ? "#fff" : "#26314a",
                  }}
                  title={`${columns[i]} × ${columns[j]}: ${v ?? "—"}`}
                >
                  {v !== null ? v.toFixed(2) : "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
