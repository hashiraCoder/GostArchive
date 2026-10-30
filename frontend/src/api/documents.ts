import { apiFetch } from "./client";

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  byte_size: number;
  status: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}

interface DocumentUploadResponse {
  document: DocumentItem;
  duplicate: boolean;
}

export function listDocuments(): Promise<DocumentListResponse> {
  return apiFetch<DocumentListResponse>("/documents");
}

export function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<DocumentUploadResponse>("/documents", {
    method: "POST",
    body: formData,
  });
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiFetch<unknown>(`/documents/${encodeURIComponent(documentId)}`, {
    method: "DELETE",
  });
}
