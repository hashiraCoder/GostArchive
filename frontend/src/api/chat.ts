import { apiFetch } from "./client";

export interface Citation {
  chunk_id: string;
  document_id: string;
  filename: string;
  document_title?: string | null;
  page_number: number | null;
  excerpt: string;
  evidence_type?: string;
}

export interface ChatResponse {
  answer: string;
  direct_answer?: string;
  archive_context?: string | null;
  limitations?: string[];
  insufficient_evidence: boolean;
  citations: Citation[];
  retrieval_count: number;
  model: string;
}

export function askQuestion(question: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: 5 }),
  });
}
