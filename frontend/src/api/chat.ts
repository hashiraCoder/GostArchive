import { apiFetch } from "./client";

export interface Citation {
  chunk_id: string;
  document_id: string;
  filename: string;
  document_title?: string | null;
  page_number: number | null;
  excerpt: string;
  evidence_type?: string;
  document_exists?: boolean;
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
  conversation_id?: string;
  message_id?: string;
  client_turn_id?: string;
}

export function askQuestion(
  question: string,
  documentIds?: string[],
  conversationId?: string,
  clientTurnId?: string,
): Promise<ChatResponse> {
  const payload: Record<string, unknown> = { question, top_k: 5 };
  if (documentIds && documentIds.length > 0) {
    payload.document_ids = documentIds;
  }
  if (conversationId) {
    payload.conversation_id = conversationId;
  }
  if (clientTurnId) {
    payload.client_turn_id = clientTurnId;
  }
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
