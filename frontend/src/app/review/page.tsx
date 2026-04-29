"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Container,
  Title,
  Text,
  Button,
  Group,
  Stack,
  Badge,
  Alert,
  Loader,
  Accordion,
  ActionIcon,
} from "@mantine/core";
import { IconAlertCircle, IconArrowRight, IconTrash } from "@tabler/icons-react";
import { listDocuments, listQuestions, deleteDocument } from "@/lib/api";
import type { Document, Question } from "@/lib/api";

export default function ReviewPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [questionsByDoc, setQuestionsByDoc] = useState<Record<string, Question[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [docs, questions] = await Promise.all([listDocuments(), listQuestions()]);
        setDocuments(docs);
        const grouped: Record<string, Question[]> = {};
        for (const q of questions) {
          if (!grouped[q.document_id]) grouped[q.document_id] = [];
          grouped[q.document_id].push(q);
        }
        setQuestionsByDoc(grouped);
      } catch (e) {
        setError(e instanceof Error ? e.message : "データの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleDelete(id: string) {
    setDeleteError(null);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (e) {
      setDeleteError(e instanceof Error ? e.message : "削除に失敗しました");
    }
  }

  if (loading) {
    return (
      <Container size="md" py="xl">
        <Group justify="center">
          <Loader />
        </Group>
      </Container>
    );
  }

  if (error) {
    return (
      <Container size="md" py="xl">
        <Alert icon={<IconAlertCircle size={16} />} color="red">
          {error}
        </Alert>
      </Container>
    );
  }

  if (documents.length === 0) {
    return (
      <Container size="md" py="xl">
        <Title order={2} mb="xl">
          問題一覧
        </Title>
        <Text c="dimmed" ta="center">
          資料がありません。
        </Text>
      </Container>
    );
  }

  return (
    <Container size="md" py="xl">
      <Title order={2} mb="xl">
        問題一覧
      </Title>

      {deleteError && (
        <Alert icon={<IconAlertCircle size={16} />} color="red" mb="md" withCloseButton onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      <Accordion variant="separated" radius="md">
        {documents.map((doc) => {
          const qs = questionsByDoc[doc.id] ?? [];
          return (
            <Accordion.Item key={doc.id} value={doc.id}>
              <Box style={{ display: "flex", alignItems: "center" }}>
                <Accordion.Control style={{ flex: 1, minWidth: 0 }}>
                  <Text fw={500} truncate>
                    {doc.file_name}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {new Date(doc.created_at).toLocaleString("ja-JP")}
                  </Text>
                </Accordion.Control>
                <Group gap="xs" wrap="nowrap" pr="md">
                  <Badge variant="light" color={qs.length > 0 ? "blue" : "gray"}>
                    {qs.length}問
                  </Badge>
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    onClick={() => handleDelete(doc.id)}
                    aria-label="削除"
                  >
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              </Box>

              <Accordion.Panel>
                {qs.length === 0 ? (
                  <Text size="sm" c="dimmed">
                    まだ問題が生成されていません。ホームから問題を生成してください。
                  </Text>
                ) : (
                  <Stack gap="sm">
                    <Stack gap={4}>
                      {qs.map((q, i) => (
                        <Text size="sm" key={q.id}>
                          {i + 1}. {q.body}
                        </Text>
                      ))}
                    </Stack>
                    <Group justify="flex-end" mt="xs">
                      <Button
                        rightSection={<IconArrowRight size={16} />}
                        onClick={() => router.push(`/quiz/${doc.id}`)}
                      >
                        再演習する
                      </Button>
                    </Group>
                  </Stack>
                )}
              </Accordion.Panel>
            </Accordion.Item>
          );
        })}
      </Accordion>
    </Container>
  );
}