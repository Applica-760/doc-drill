"use client";

import { useState } from "react";
import { Container, Stepper, Button, Group } from "@mantine/core";
import DocumentUpload from "@/components/DocumentUpload";
import DocumentSelect from "@/components/DocumentSelect";
import type { Document } from "@/lib/api";

export default function Home() {
  const [active, setActive] = useState(0);
  const [uploadedDoc, setUploadedDoc] = useState<Document | null>(null);

  function handleUploaded(doc: Document) {
    setUploadedDoc(doc);
    setActive(1);
  }

  return (
    <Container size="md" className="py-12">
      <Stepper active={active} onStepClick={setActive}>
        <Stepper.Step label="資料をアップロード" description="PDFを選択">
          <div className="mt-6">
            <DocumentUpload onUploaded={handleUploaded} />
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={() => setActive(1)}>
                スキップ（既存の資料を使う）
              </Button>
            </Group>
          </div>
        </Stepper.Step>

        <Stepper.Step label="資料を選んで問題を生成" description="問題数を指定して開始">
          <div className="mt-6">
            <DocumentSelect newDocument={uploadedDoc} />
          </div>
        </Stepper.Step>
      </Stepper>
    </Container>
  );
}
