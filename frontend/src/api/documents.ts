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
  error_code?: string | null;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}

export interface DocumentUploadResponse {
  document: DocumentItem;
  duplicate: boolean;
}

export interface BulkDeleteResultItem {
  id: string;
  success: boolean;
  error?: string | null;
}

export interface BulkDeleteResponse {
  results: BulkDeleteResultItem[];
  total_deleted: number;
}

export interface ListDocumentsParams {
  query?: string;
  status?: string;
  file_type?: string;
  limit?: number;
  offset?: number;
}

export function listDocuments(params?: ListDocumentsParams): Promise<DocumentListResponse> {
  if (!params) {
    return apiFetch<DocumentListResponse>("/documents");
  }
  const searchParams = new URLSearchParams();
  if (params.query) searchParams.set("query", params.query);
  if (params.status) searchParams.set("status", params.status);
  if (params.file_type) searchParams.set("file_type", params.file_type);
  if (params.limit !== undefined) searchParams.set("limit", String(params.limit));
  if (params.offset !== undefined) searchParams.set("offset", String(params.offset));

  const qs = searchParams.toString();
  return apiFetch<DocumentListResponse>(qs ? `/documents?${qs}` : "/documents");
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

export function bulkDeleteDocuments(documentIds: string[]): Promise<BulkDeleteResponse> {
  return apiFetch<BulkDeleteResponse>("/documents/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds }),
  });
}
