"use client";
// DataFrame プレビューテーブル
export default function DataTable({
  rows,
  maxRows = 100,
}: {
  rows: Record<string, unknown>[];
  maxRows?: number;
}) {
  if (!rows.length) {
    return <p className="p-4 text-sm text-[var(--muted)]">データがありません</p>;
  }
  const columns = Object.keys(rows[0]);
  const fmt = (v: unknown): string => {
    if (v === null || v === undefined) return "";
    if (typeof v === "number" && !Number.isInteger(v)) return v.toPrecision(4);
    return String(v);
  };
  return (
    <div className="h-full overflow-auto">
      <table className="data-table w-full">
        <thead>
          <tr>
            <th>#</th>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, maxRows).map((row, i) => (
            <tr key={i}>
              <td className="text-[var(--muted)]">{i + 1}</td>
              {columns.map((c) => (
                <td key={c}>{fmt(row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
