"use client";
// 合言葉入力ゲート(バックエンドで検証)
import { useState } from "react";
import { useApp } from "@/lib/store";

export default function PasscodeGate() {
  const { login } = useApp();
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || busy) return;
    setBusy(true);
    setError("");
    try {
      await login(code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "認証に失敗しました");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center">
      <form onSubmit={submit} className="panel w-[400px] p-8">
        <div className="mb-1 text-2xl font-bold">🧪 Material AI Platform</div>
        <p className="mb-6 text-sm text-[var(--muted)]">
          材料開発向け 特性予測・データ解析(デモ)
        </p>
        <label className="mb-2 block text-sm">🔒 合言葉を入力してください</label>
        <input
          type="password"
          className="input mb-3 w-full"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          autoFocus
        />
        {error && <p className="mb-3 text-sm text-[var(--bad)]">{error}</p>}
        <button type="submit" className="btn w-full" disabled={busy || !code}>
          {busy ? "確認中..." : "入室"}
        </button>
      </form>
    </div>
  );
}
