import type { Metadata } from "next";
import "./globals.css";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { AppProvider } from "@/lib/store";
import Shell from "@/components/Shell";

export const metadata: Metadata = {
  title: "Material AI Platform",
  description: "材料開発向け 特性予測・データ解析プラットフォーム(デモ)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="h-full">
      <body className="min-h-full">
        <AppProvider>
          <Shell>{children}</Shell>
        </AppProvider>
      </body>
    </html>
  );
}
