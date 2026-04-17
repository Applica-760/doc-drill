"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  Text,
  Button,
  Group,
  NumberInput,
  ActionIcon,
  Alert,
  Loader,
  Stack,
} from "@mantine/core";
import { IconTrash, IconAlertCircle, IconArrowRight } from "@tabler/icons-react";
import { listDocuments, deleteDocument, generateQuestions } from "@/lib/api";
import type { Document } from "@/lib/api";

const QUESTION_COUNT_MIN = 1;
const QUESTION_COUNT_MAX = 20;
const QUESTION_COUNT_DEFAULT = 5;

type Props = {
  newDocument: Document | null;
};

export default function DocumentSelect({ newDocument }: Props) {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [fetchLoading, setFetchLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [count, setCount] = useState<number>(QUESTION_COUNT_DEFAULT);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  // 新規アップロードされた資料をリストに即時反映する
  useEffect(() => {
    if (!newDocument) return;
    setDocuments((prev) => {
      const exists = prev.some((d) => d.id === newDocument.id);
      return exists ? prev : [newDocument, ...prev];
    });
    setSelectedId(newDocument.id);
  }, [newDocument]);

  async function loadDocuments() {
    setFetchLoading(true);
    setFetchError(null);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : "資料の取得に失敗しました");
    } finally {
      setFetchLoading(false);
    }
  }

  async function handleDelete(id: string) {
    setDeleteError(null);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      if (selectedId === id) setSelectedId(null);
    } catch (e) {
      setDeleteError(e instanceof Error ? e.message : "削除に失敗しました");
    }
  }

  async function handleGenerate() {
    if (!selectedId) return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const questions = await generateQuestions(selectedId, count);
      sessionStorage.setItem(`quiz_${selectedId}`, JSON.stringify(questions));
      router.push(`/quiz/${selectedId}`);
    } catch (e) {
      setGenerateError(e instanceof Error ? e.message : "問題生成に失敗しました");
      setGenerating(false);
    }
  }

  if (fetchLoading) {
    return (
      <Group justify="center" py="xl">
        <Loader />
      </Group>
    );
  }

  if (fetchError) {
    return (
      <Alert icon={<IconAlertCircle size={16} />} color="red">
        {fetchError}
      </Alert>
    );
  }

  if (documents.length === 0) {
    return (
      <Text c="dimmed" ta="center" py="xl">
        アップロード済みの資料がありません。Step 1 でPDFをアップロードしてください。
      </Text>
    );
  }

  return (
    <Stack gap="md">
      {deleteError && (
        <Alert icon={<IconAlertCircle size={16} />} color="red" withCloseButton onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}
      {documents.map((doc) => (
        <Card
          key={doc.id}
          withBorder
          radius="md"
          style={{
            cursor: "pointer",
            borderColor:
              selectedId === doc.id
                ? "var(--mantine-color-blue-6)"
                : undefined,
            borderWidth: selectedId === doc.id ? 2 : 1,
          }}
          onClick={() => setSelectedId(doc.id)}
        >
          <Group justify="space-between" wrap="nowrap">
            <div style={{ minWidth: 0 }}>
              <Text fw={500} truncate>
                {doc.file_name}
              </Text>
              <Text size="xs" c="dimmed">
                {new Date(doc.created_at).toLocaleString("ja-JP")}
              </Text>
            </div>
            <ActionIcon
              variant="subtle"
              color="red"
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(doc.id);
              }}
              aria-label="削除"
            >
              <IconTrash size={16} />
            </ActionIcon>
          </Group>
        </Card>
      ))}

      <Card withBorder radius="md" mt="xs">
        <Group align="flex-end" gap="md" wrap="wrap">
          <NumberInput
            label="問題数"
            description={`${QUESTION_COUNT_MIN}〜${QUESTION_COUNT_MAX}問`}
            min={QUESTION_COUNT_MIN}
            max={QUESTION_COUNT_MAX}
            value={count}
            onChange={(v) => setCount(typeof v === "number" ? v : QUESTION_COUNT_DEFAULT)}
            style={{ width: 120 }}
          />
          <Button
            leftSection={<IconArrowRight size={16} />}
            disabled={!selectedId}
            loading={generating}
            onClick={handleGenerate}
          >
            問題を生成して解く
          </Button>
        </Group>
        {generateError && (
          <Alert icon={<IconAlertCircle size={16} />} color="red" mt="sm">
            {generateError}
          </Alert>
        )}
      </Card>
    </Stack>
  );
}
