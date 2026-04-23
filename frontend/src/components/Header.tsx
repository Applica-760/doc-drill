"use client";

import Link from "next/link";
import { Container, Group, Anchor } from "@mantine/core";

export default function Header() {
  return (
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
  );
}
