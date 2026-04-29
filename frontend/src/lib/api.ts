import type { components } from "./api.gen";

export type Document = components["schemas"]["DocumentResponse"];
export type Question = components["schemas"]["QuestionResponse"];
export type GenerateQuestionsRequest = components["schemas"]["GenerateQuestionsRequest"];
export type CreateLocalDocumentRequest = components["schemas"]["CreateLocalDocumentRequest"];
export type QuestionImportItem = components["schemas"]["ShortAnswerQuestion"];

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const quizSessionKey = (documentId: string) => `quiz_${documentId}`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    // FormData の場合は Content-Type をブラウザに任せる（boundary が自動付与される）
    headers: isFormData
      ? init?.headers
      : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Documents ────────────────────────────────────────────────────────────────

export function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  return request<Document>("/documents", { method: "POST", body: form });
}

export function listDocuments(): Promise<Document[]> {
  return request<Document[]>("/documents");
}

export function deleteDocument(id: string): Promise<void> {
  return request<void>(`/documents/${id}`, { method: "DELETE" });
}

export function createLocalDocument(name: string): Promise<Document> {
  return request<Document>("/documents/local", {
    method: "POST",
    body: JSON.stringify({ name } satisfies CreateLocalDocumentRequest),
  });
}

export function importQuestions(
  documentId: string,
  items: QuestionImportItem[]
): Promise<Question[]> {
  return request<Question[]>(`/documents/${documentId}/questions/import`, {
    method: "POST",
    body: JSON.stringify(items),
  });
}

// ── Questions ────────────────────────────────────────────────────────────────

export function generateQuestions(
  documentId: string,
  count: number
): Promise<Question[]> {
  return request<Question[]>("/questions/generate", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, count } satisfies GenerateQuestionsRequest),
  });
}

export function listQuestions(documentId?: string): Promise<Question[]> {
  const params = documentId ? `?document_id=${documentId}` : "";
  return request<Question[]>(`/questions${params}`);
}
