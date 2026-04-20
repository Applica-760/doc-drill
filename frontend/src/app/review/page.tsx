"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
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
} from "@mantine/core";
import { IconAlertCircle, IconArrowRight } from "@tabler/icons-react";
import { listDocuments, listQuestions } from "@/lib/api";
import type { Document, Question } from "@/lib/api";

export default function ReviewPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [questionsByDoc, setQuestionsByDoc] = useState<Record<string, Question[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          アップロード済みの資料がありません。
        </Text>
      </Container>
    );
  }

  return (
    <Container size="md" py="xl">
      <Title order={2} mb="xl">
        問題一覧
      </Title>

      <Accordion variant="separated" radius="md">
        {documents.map((doc) => {
          const qs = questionsByDoc[doc.id] ?? [];
          return (
            <Accordion.Item key={doc.id} value={doc.id}>
              <Accordion.Control>
                <Group justify="space-between" wrap="nowrap" pr="md">
                  <div style={{ minWidth: 0 }}>
                    <Text fw={500} truncate>
                      {doc.file_name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(doc.created_at).toLocaleString("ja-JP")}
                    </Text>
                  </div>
                  <Badge variant="light" color={qs.length > 0 ? "blue" : "gray"}>
                    {qs.length}問
                  </Badge>
                </Group>
              </Accordion.Control>

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
