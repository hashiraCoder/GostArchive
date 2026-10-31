import { apiFetch } from "./client";

export interface CitationSnapshot {
  chunk_id: string;
  document_id: string;
  filename: string;
  document_title?: string | null;
  page_number: number | null;
  excerpt: string;
  evidence_type?: string;
  document_exists: boolean;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  client_turn_id?: string | null;
  role: "user" | "assistant";
  content: string;
  status: "pending" | "completed" | "failed";
  direct_answer?: string | null;
  archive_context?: string | null;
  limitations: string[];
  insufficient_evidence: boolean;
  citations: CitationSnapshot[];
  retrieval_count: number;
  model?: string | null;
  error_message?: string | null;
  scope_document_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string | null;
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  total: number;
}

export interface ConversationDetailResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

export function listConversations(
  limit: number = 20,
  offset: number = 0,
): Promise<ConversationListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  return apiFetch<ConversationListResponse>(`/conversations?${params.toString()}`);
}

export function getConversation(id: string): Promise<ConversationDetailResponse> {
  return apiFetch<ConversationDetailResponse>(`/conversations/${encodeURIComponent(id)}`);
}

export function createConversation(title?: string): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>("/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title || null }),
  });
}

export function updateConversation(id: string, title: string): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`/conversations/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export function deleteConversation(id: string): Promise<void> {
  return apiFetch<void>(`/conversations/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}
