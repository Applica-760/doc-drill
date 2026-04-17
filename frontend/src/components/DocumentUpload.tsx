"use client";

import { useState } from "react";
import { Group, Text, Alert } from "@mantine/core";
import { Dropzone, PDF_MIME_TYPE } from "@mantine/dropzone";
import { IconUpload, IconFile, IconX, IconAlertCircle } from "@tabler/icons-react";
import { uploadDocument } from "@/lib/api";
import type { Document } from "@/lib/api";

type Props = {
  onUploaded: (doc: Document) => void;
};

export default function DocumentUpload({ onUploaded }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDrop(files: File[]) {
    const file = files[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const doc = await uploadDocument(file);
      onUploaded(doc);
    } catch (e) {
      setError(e instanceof Error ? e.message : "アップロードに失敗しました");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Dropzone
        onDrop={handleDrop}
        accept={PDF_MIME_TYPE}
        maxFiles={1}
        loading={loading}
        maxSize={20 * 1024 * 1024}
      >
        <Group justify="center" gap="xl" mih={120} style={{ pointerEvents: "none" }}>
          <Dropzone.Accept>
            <IconUpload size={48} stroke={1.5} color="var(--mantine-color-blue-6)" />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <IconX size={48} stroke={1.5} color="var(--mantine-color-red-6)" />
          </Dropzone.Reject>
          <Dropzone.Idle>
            <IconFile size={48} stroke={1.5} color="var(--mantine-color-dimmed)" />
          </Dropzone.Idle>
          <div>
            <Text size="lg" fw={500}>
              PDFをドロップ、またはクリックして選択
            </Text>
            <Text size="sm" c="dimmed" mt={4}>
              1ファイル・PDF形式・最大20MB
            </Text>
          </div>
        </Group>
      </Dropzone>

      {error && (
        <Alert icon={<IconAlertCircle size={16} />} color="red" mt="sm">
          {error}
        </Alert>
      )}
    </div>
  );
}
