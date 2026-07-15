"use client";
// サイドバーナビゲーション(デスクトップ版と同じ構成)
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/store";

const PAGES = [
  { href: "/", label: "ダッシュボード" },
  { href: "/data", label: "データ管理" },
  { href: "/analysis", label: "特徴量解析" },
  { href: "/predict", label: "特性予測" },
  { href: "/report", label: "レポート" },
];

const FUTURE = ["最適化(将来)", "実験計画(将来)"];

export default function Sidebar() {
  const pathname = usePathname();
  const { data, result, logout } = useApp();

  return (
    <aside className="flex w-[210px] shrink-0 flex-col bg-[#101a2b] px-2 py-4">
      <div className="mb-5 px-3 text-[15px] font-bold">
        🧪 Material AI Platform
      </div>
      <nav className="flex flex-col gap-1">
        {PAGES.map((p) => {
          const active = pathname === p.href;
          return (
            <Link
              key={p.href}
              href={p.href}
              className={`rounded-md px-4 py-2.5 text-[13px] transition-colors ${
                active
                  ? "bg-[var(--accent)] text-white"
                  : "hover:bg-[#182a45]"
              }`}
            >
              {p.label}
            </Link>
          );
        })}
        {FUTURE.map((label) => (
          <span
            key={label}
            className="cursor-not-allowed rounded-md px-4 py-2.5 text-[13px] text-[#4a5670]"
          >
            {label}
          </span>
        ))}
      </nav>
      <div className="mt-auto space-y-2 border-t border-[var(--border)] px-3 pt-4 text-xs text-[var(--muted)]">
        <div>
          データ:{" "}
          <span className="text-[var(--text)]">{data ? data.name : "未読込"}</span>
        </div>
        <div>
          最新モデル R²:{" "}
          <span className="text-[var(--good)]">
            {result ? result.metrics.r2.toFixed(3) : "—"}
          </span>
        </div>
        <button onClick={logout} className="text-[var(--muted)] underline">
          ログアウト
        </button>
        <div className="pt-2 text-[10px] leading-relaxed">
          ⚠️ デモ用途。データはセッション中のみ保持され、機密データはアップロードしないでください。
        </div>
      </div>
    </aside>
  );
}
