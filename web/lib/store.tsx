"use client";
// アプリ全体の状態管理(合言葉・データ・学習結果)
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, type DataInfo, type TrainResult } from "./api";

type AppState = {
  passcode: string | null;
  login: (passcode: string) => Promise<void>;
  logout: () => void;
  data: DataInfo | null;
  setData: (d: DataInfo | null, opts?: { keepResult?: boolean }) => void;
  result: TrainResult | null;
  setResult: (r: TrainResult | null) => void;
  restoring: boolean;
};

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [passcode, setPasscode] = useState<string | null>(null);
  const [data, setDataState] = useState<DataInfo | null>(null);
  const [result, setResult] = useState<TrainResult | null>(null);
  const [restoring, setRestoring] = useState(true);

  // リロード時の復元(合言葉と sid は sessionStorage に保持)
  useEffect(() => {
    const saved = sessionStorage.getItem("mai_passcode");
    const sid = sessionStorage.getItem("mai_sid");
    if (!saved) {
      setRestoring(false);
      return;
    }
    setPasscode(saved);
    if (sid) {
      api<DataInfo>(`/api/data/${sid}`, { passcode: saved })
        .then((d) => setDataState(d))
        .catch(() => sessionStorage.removeItem("mai_sid"))
        .finally(() => setRestoring(false));
    } else {
      setRestoring(false);
    }
  }, []);

  const login = useCallback(async (code: string) => {
    await api("/api/auth/verify", { body: { passcode: code } });
    sessionStorage.setItem("mai_passcode", code);
    setPasscode(code);
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem("mai_passcode");
    sessionStorage.removeItem("mai_sid");
    setPasscode(null);
    setDataState(null);
    setResult(null);
  }, []);

  const setData = useCallback(
    (d: DataInfo | null, opts?: { keepResult?: boolean }) => {
      setDataState(d);
      if (!opts?.keepResult) setResult(null); // 新データ読込時は学習結果を破棄
      if (d) sessionStorage.setItem("mai_sid", d.sid);
      else sessionStorage.removeItem("mai_sid");
    },
    [],
  );

  return (
    <Ctx.Provider
      value={{ passcode, login, logout, data, setData, result, setResult, restoring }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useApp は AppProvider の内側で使用してください");
  return ctx;
}
