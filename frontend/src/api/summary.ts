import { apiFetch } from "./client";

export interface SummaryDocument {
  document_id: string;
  filename: string;
  chunk_count: number;
}

export interface SummaryResponse {
  summary: string;
  scope: string;
  inspected_documents: SummaryDocument[];
  limitations: string[];
  model: string;
}

export function summarizeArchive(documentId?: string): Promise<SummaryResponse> {
  return apiFetch<SummaryResponse>("/summarize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId ?? null, max_chunks: 12 }),
  });
}
