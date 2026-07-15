// 数値指標タイル
export default function MetricTile({
  label,
  value,
  color = "var(--good)",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="panel px-5 py-3">
      <div className="text-xs text-[var(--muted)]">{label}</div>
      <div className="text-2xl font-bold" style={{ color }}>
        {value}
      </div>
    </div>
  );
}
