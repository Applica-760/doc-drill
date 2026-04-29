"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { TextInput, Textarea, Button, Group, Stack, Alert, Text } from "@mantine/core";
import { IconAlertCircle, IconDownload, IconUpload } from "@tabler/icons-react";
import { createLocalDocument, importQuestions } from "@/lib/api";
import type { QuestionImportItem } from "@/lib/api";

const TEMPLATE: QuestionImportItem[] = [
  {
    question_type: "short_answer",
    body: "問題文",
    answer: "解答",
    explanation: "解説",
    options: null,
  },
];

export default function LocalImport() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [jsonText, setJsonText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function downloadTemplate() {
    const blob = new Blob([JSON.stringify(TEMPLATE, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "template.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setJsonText((ev.target?.result as string) ?? "");
      setError(null);
    };
    reader.readAsText(file, "utf-8");
    // 同じファイルを再選択できるようリセット
    e.target.value = "";
  }

  async function handleImport() {
    setError(null);

    if (!name.trim()) {
      setError("ドキュメント名を入力してください");
      return;
    }

    let items: QuestionImportItem[];
    try {
      const parsed = JSON.parse(jsonText);
      if (!Array.isArray(parsed)) throw new Error("配列形式で入力してください");
      items = parsed as QuestionImportItem[];
    } catch (e) {
      setError(e instanceof Error ? e.message : "JSONの形式が正しくありません");
      return;
    }

    setLoading(true);
    try {
      const doc = await createLocalDocument(name.trim());
      await importQuestions(doc.id, items);
      router.push("/review");
    } catch (e) {
      setError(e instanceof Error ? e.message : "インポートに失敗しました");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Stack mt="lg" gap="md">
      <TextInput
        label="問題セット名"
        placeholder="例: インフラ基礎知識"
        value={name}
        onChange={(e) => setName(e.currentTarget.value)}
        required
      />

      <div>
        <Group justify="space-between" mb={4}>
          <Text size="sm" fw={500}>
            問題JSON
          </Text>
          <Group gap="xs">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,application/json"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <Button
              size="xs"
              variant="subtle"
              leftSection={<IconUpload size={14} />}
              onClick={() => fileInputRef.current?.click()}
            >
              JSONファイルを読み込む
            </Button>
            <Button
              size="xs"
              variant="subtle"
              leftSection={<IconDownload size={14} />}
              onClick={downloadTemplate}
            >
              テンプレートをダウンロード
            </Button>
          </Group>
        </Group>
        <Textarea
          placeholder={JSON.stringify(TEMPLATE, null, 2)}
          value={jsonText}
          onChange={(e) => setJsonText(e.currentTarget.value)}
          autosize
          minRows={8}
          maxRows={20}
          styles={{ input: { fontFamily: "monospace", fontSize: "12px" } }}
        />
      </div>

      {error && (
        <Alert icon={<IconAlertCircle size={16} />} color="red">
          {error}
        </Alert>
      )}

      <Group justify="flex-end">
        <Button onClick={handleImport} loading={loading} disabled={!name || !jsonText}>
          インポート
        </Button>
      </Group>
    </Stack>
  );
}