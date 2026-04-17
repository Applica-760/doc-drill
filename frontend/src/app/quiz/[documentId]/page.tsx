"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Container,
  Title,
  Text,
  Button,
  Group,
  Stack,
  Card,
  Badge,
  Progress,
  Alert,
  Divider,
  Loader,
} from "@mantine/core";
import { IconCheck, IconX, IconAlertCircle, IconHome } from "@tabler/icons-react";
import { listQuestions } from "@/lib/api";
import type { Question } from "@/lib/api";

type Result = "correct" | "incorrect" | null;

type Props = {
  params: Promise<{ documentId: string }>;
};

export default function QuizPage({ params }: Props) {
  const { documentId } = use(params);
  const router = useRouter();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [results, setResults] = useState<Result[]>([]);
  const [phase, setPhase] = useState<"quiz" | "complete">("quiz");

  useEffect(() => {
    async function load() {
      const stored = sessionStorage.getItem(`quiz_${documentId}`);
      if (stored) {
        const qs: Question[] = JSON.parse(stored);
        setQuestions(qs);
        setResults(new Array(qs.length).fill(null));
        setLoading(false);
        return;
      }
      try {
        const qs = await listQuestions(documentId);
        setQuestions(qs);
        setResults(new Array(qs.length).fill(null));
      } catch (e) {
        setError(e instanceof Error ? e.message : "問題の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [documentId]);

  function handleResult(result: "correct" | "incorrect") {
    const newResults = [...results];
    newResults[currentIndex] = result;
    setResults(newResults);

    if (currentIndex + 1 < questions.length) {
      setCurrentIndex((i) => i + 1);
      setShowAnswer(false);
    } else {
      setResults(newResults);
      setPhase("complete");
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

  if (questions.length === 0) {
    return (
      <Container size="md" py="xl">
        <Text c="dimmed" ta="center">
          問題が見つかりません。ホームに戻って問題を生成してください。
        </Text>
        <Group justify="center" mt="md">
          <Button leftSection={<IconHome size={16} />} variant="light" onClick={() => router.push("/")}>
            ホームに戻る
          </Button>
        </Group>
      </Container>
    );
  }

  // ── 完了画面 ────────────────────────────────────────────────────────────────
  if (phase === "complete") {
    const correctCount = results.filter((r) => r === "correct").length;
    const total = questions.length;
    const pct = Math.round((correctCount / total) * 100);

    return (
      <Container size="md" py="xl">
        <Stack gap="lg">
          <Title order={2} ta="center">
            結果
          </Title>
          <Card withBorder radius="md" p="xl" ta="center">
            <Text size="xl" fw={700}>
              {correctCount} / {total} 問正解
            </Text>
            <Text size="sm" c="dimmed" mb="md">
              正答率 {pct}%
            </Text>
            <Progress value={pct} size="lg" radius="xl" color={pct >= 70 ? "green" : pct >= 40 ? "yellow" : "red"} />
          </Card>

          <Stack gap="sm">
            {questions.map((q, i) => (
              <Card key={q.id} withBorder radius="md" p="md">
                <Group justify="space-between" wrap="nowrap" align="flex-start">
                  <Stack gap={4} style={{ minWidth: 0, flex: 1 }}>
                    <Text size="sm" fw={500} lineClamp={2}>
                      {i + 1}. {q.body}
                    </Text>
                    <Text size="xs" c="dimmed">
                      正解: {q.answer}
                    </Text>
                  </Stack>
                  <Badge
                    color={results[i] === "correct" ? "green" : "red"}
                    variant="light"
                    style={{ flexShrink: 0 }}
                  >
                    {results[i] === "correct" ? "正解" : "不正解"}
                  </Badge>
                </Group>
              </Card>
            ))}
          </Stack>

          <Group justify="center">
            <Button leftSection={<IconHome size={16} />} variant="light" onClick={() => router.push("/")}>
              ホームに戻る
            </Button>
          </Group>
        </Stack>
      </Container>
    );
  }

  // ── 問題画面 ────────────────────────────────────────────────────────────────
  const question = questions[currentIndex];
  const progress = (currentIndex / questions.length) * 100;

  return (
    <Container size="md" py="xl">
      <Stack gap="lg">
        <Stack gap="xs">
          <Group justify="space-between">
            <Text size="sm" c="dimmed">
              問題 {currentIndex + 1} / {questions.length}
            </Text>
          </Group>
          <Progress value={progress} size="sm" radius="xl" />
        </Stack>

        <Card withBorder radius="md" p="xl">
          <Text fw={500} size="lg">
            {question.body}
          </Text>
        </Card>

        {!showAnswer ? (
          <Group justify="center">
            <Button onClick={() => setShowAnswer(true)}>答えを確認</Button>
          </Group>
        ) : (
          <Stack gap="md">
            <Divider label="解答・解説" labelPosition="center" />
            <Card withBorder radius="md" p="md" bg="var(--mantine-color-blue-0)">
              <Stack gap="xs">
                <Text size="sm" c="dimmed" fw={500}>
                  正解
                </Text>
                <Text fw={600}>{question.answer}</Text>
                {question.explanation && (
                  <>
                    <Text size="sm" c="dimmed" fw={500} mt="xs">
                      解説
                    </Text>
                    <Text size="sm">{question.explanation}</Text>
                  </>
                )}
              </Stack>
            </Card>

            <Group justify="center" gap="md">
              <Button
                leftSection={<IconX size={16} />}
                color="red"
                variant="light"
                onClick={() => handleResult("incorrect")}
              >
                不正解
              </Button>
              <Button
                leftSection={<IconCheck size={16} />}
                color="green"
                variant="light"
                onClick={() => handleResult("correct")}
              >
                正解
              </Button>
            </Group>
          </Stack>
        )}
      </Stack>
    </Container>
  );
}
