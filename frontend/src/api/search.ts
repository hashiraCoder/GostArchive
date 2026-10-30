import { apiFetch } from "./client";

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number | null;
  text: string;
  start_char: number;
  end_char: number;
  score: number;
  cosine_similarity?: number;
  relevance_label?: string;
}

interface SearchResponse {
  items: SearchResult[];
  total: number;
}

export function searchDocuments(query: string): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: 5 }),
  });
}
