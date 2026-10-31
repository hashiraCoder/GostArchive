/**
 * Health and readiness API contracts.
 */
import { apiFetch } from "./client";

export type DependencyStatus = "ready" | "degraded" | "unavailable";

export interface DependencyDetail {
  status: DependencyStatus;
  message?: string | null;
}

export interface HealthResponse {
  status: "ok";
  app_version: string;
}

export interface ReadyResponse {
  overall: DependencyStatus;
  dependencies: {
    database: DependencyDetail;
    chroma: DependencyDetail;
    embedding_model: DependencyDetail;
    ollama: DependencyDetail;
    ollama_service?: DependencyDetail;
    model_available?: DependencyDetail;
    model_inference?: DependencyDetail;
    embedding_service?: DependencyDetail;
    document_storage?: DependencyDetail;
    [key: string]: DependencyDetail | undefined;
  };
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export function getReady(): Promise<ReadyResponse> {
  return apiFetch<ReadyResponse>("/ready");
}
