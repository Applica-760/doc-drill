import "@mantine/core/styles.css";
import "@mantine/dropzone/styles.css";
import "./globals.css";

import type { Metadata } from "next";
import Link from "next/link";
import { ColorSchemeScript, MantineProvider, mantineHtmlProps, Container, Group, Anchor, Text } from "@mantine/core";

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
          <header style={{ borderBottom: "1px solid var(--mantine-color-gray-3)" }}>
            <Container size="md" py="sm">
              <Group justify="space-between">
                <Anchor component={Link} href="/" fw={700} size="lg" c="inherit" underline="never">
                  Doc Drill
                </Anchor>
                <Group gap="lg">
                  <Anchor component={Link} href="/" size="sm" c="dimmed" underline="hover">
                    新しい問題
                  </Anchor>
                  <Anchor component={Link} href="/review" size="sm" c="dimmed" underline="hover">
                    問題一覧
                  </Anchor>
                </Group>
              </Group>
            </Container>
          </header>
          <main>{children}</main>
        </MantineProvider>
      </body>
    </html>
  );
}
