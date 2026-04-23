import "@mantine/core/styles.css";
import "@mantine/dropzone/styles.css";
import "./globals.css";

import type { Metadata } from "next";
import { ColorSchemeScript, MantineProvider, mantineHtmlProps } from "@mantine/core";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "Doc Drill",
  description: "資料をアップロードして問題を生成する学習アプリ",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" {...mantineHtmlProps}>
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider>
          <Header />
          <main>{children}</main>
        </MantineProvider>
      </body>
    </html>
  );
}
