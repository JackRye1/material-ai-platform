"use client";
// 画面全体の骨格: 合言葉ゲート → サイドバー + コンテンツ
import { useApp } from "@/lib/store";
import PasscodeGate from "./PasscodeGate";
import Sidebar from "./Sidebar";

export default function Shell({ children }: { children: React.ReactNode }) {
  const { passcode, restoring } = useApp();

  if (restoring) {
    return (
      <div className="flex h-screen items-center justify-center text-[var(--muted)]">
        読み込み中...
      </div>
    );
  }
  if (!passcode) return <PasscodeGate />;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0 px-6 py-5">{children}</main>
    </div>
  );
}
