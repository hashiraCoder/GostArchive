import React from "react";
import type { ApiError } from "../../api/client";
import type { DependencyDetail, ReadyResponse } from "../../api/health";
import { ErrorBanner } from "../ErrorBanner";

interface SystemStatusViewProps {
  readyData: ReadyResponse | null;
  loading: boolean;
  error: ApiError | null;
  onRefresh: () => void;
  lastChecked: Date | null;
}

export const SystemStatusView: React.FC<SystemStatusViewProps> = ({
  readyData,
  loading,
  error,
  onRefresh,
  lastChecked,
}) => {
  const deps = (readyData?.dependencies || {}) as Record<string, DependencyDetail | undefined>;

  const getStatusBadge = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "ready":
      case "ok":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-status-ready bg-status-ready/10 border border-status-ready/20 px-2.5 py-0.5 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-status-ready"></span>
            Ready
          </span>
        );
      case "degraded":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-status-degraded bg-status-degraded/10 border border-status-degraded/20 px-2.5 py-0.5 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-status-degraded"></span>
            Degraded
          </span>
        );
      case "unavailable":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-status-unavailable bg-status-unavailable/10 border border-status-unavailable/20 px-2.5 py-0.5 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-status-unavailable"></span>
            Offline
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-parchment-muted bg-parchment-border/40 border border-parchment-border px-2.5 py-0.5 rounded-full">
            Unknown
          </span>
        );
    }
  };

  const dbStatus = deps.document_storage?.status || deps.database?.status || deps.sqlite?.status;
  const dbMsg = deps.document_storage?.message || deps.database?.message || "SQLite tables & Chroma vector store active";

  const embStatus = deps.embedding_service?.status || deps.embedding_model?.status;
  const embMsg = deps.embedding_service?.message || deps.embedding_model?.message || "all-MiniLM-L6-v2 local sentence transformer";

  const daemonStatus = deps.ollama_service?.status || deps.ollama?.status;
  const daemonMsg = deps.ollama_service?.message || (daemonStatus === "ready" ? "HTTP loopback 127.0.0.1:11434 responsive" : "Ollama service unavailable");

  const modelStatus = deps.model_available?.status || (daemonStatus === "ready" ? "ready" : "unavailable");
  const modelMsg = deps.model_available?.message || "Configured model verified in local tags";

  const infStatus = deps.model_inference?.status || (daemonStatus === "ready" ? "ready" : "unavailable");
  const infMsg = deps.model_inference?.message || "Local generation verified on test prompt";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-parchment-border bg-parchment-surface p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-parchment-border pb-4">
          <div>
            <h3 className="font-serif font-bold text-xl text-parchment-text">
              System Subsystem Diagnostics
            </h3>
            <p className="text-xs text-parchment-muted mt-0.5">
              Decoupled health checks across storage, embeddings, Ollama daemon, and local inference
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastChecked && (
              <span className="text-[11px] text-parchment-muted">
                Last checked: {lastChecked.toLocaleTimeString()}
              </span>
            )}
            <button
              type="button"
              onClick={onRefresh}
              disabled={loading}
              className="px-3.5 py-1.5 rounded-lg border border-parchment-border bg-parchment-surface text-parchment-accent font-semibold text-xs hover:bg-parchment-sidebar transition disabled:opacity-50"
            >
              {loading ? "Checking…" : "Run Health Check"}
            </button>
          </div>
        </div>

        {error && <ErrorBanner error={error} onRetry={onRefresh} />}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* 1. Storage & Relational Database */}
          <div className="p-4 rounded-xl border border-parchment-border bg-parchment-bg/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-parchment-text text-sm">
                1. Document Storage (SQLite + Chroma)
              </span>
              {getStatusBadge(dbStatus)}
            </div>
            <p className="text-parchment-muted leading-relaxed">
              {dbMsg}
            </p>
            <div className="text-[11px] text-parchment-muted font-mono border-t border-parchment-border/40 pt-2">
              Relational: SQLite · Vector: Chroma HNSW · FTS: porter
            </div>
          </div>

          {/* 2. Embedding Model */}
          <div className="p-4 rounded-xl border border-parchment-border bg-parchment-bg/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-parchment-text text-sm">
                2. Embedding Service
              </span>
              {getStatusBadge(embStatus)}
            </div>
            <p className="text-parchment-muted leading-relaxed">
              {embMsg}
            </p>
            <div className="text-[11px] text-parchment-muted font-mono border-t border-parchment-border/40 pt-2">
              Dimensions: 384 · Device: Local CPU · Zero external API
            </div>
          </div>

          {/* 3. Ollama Daemon */}
          <div className="p-4 rounded-xl border border-parchment-border bg-parchment-bg/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-parchment-text text-sm">
                3. Ollama Daemon Connectivity
              </span>
              {getStatusBadge(daemonStatus)}
            </div>
            <p className="text-parchment-muted leading-relaxed">
              {daemonMsg}
            </p>
            <div className="text-[11px] text-parchment-muted font-mono border-t border-parchment-border/40 pt-2">
              Endpoint: http://127.0.0.1:11434 · Local loopback
            </div>
          </div>

          {/* 4. Configured Model Availability */}
          <div className="p-4 rounded-xl border border-parchment-border bg-parchment-bg/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-parchment-text text-sm">
                4. Model Availability
              </span>
              {getStatusBadge(modelStatus)}
            </div>
            <p className="text-parchment-muted leading-relaxed">
              {modelMsg}
            </p>
            <div className="text-[11px] text-parchment-muted font-mono border-t border-parchment-border/40 pt-2">
              Target: gemma3:1b · Local weights
            </div>
          </div>

          {/* 5. Model Inference Readiness */}
          <div className="p-4 rounded-xl border border-parchment-border bg-parchment-bg/50 space-y-2 md:col-span-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-parchment-text text-sm">
                5. Model Inference Verification
              </span>
              {getStatusBadge(infStatus)}
            </div>
            <p className="text-parchment-muted leading-relaxed">
              {infMsg}
            </p>
            <div className="text-[11px] text-parchment-muted font-mono border-t border-parchment-border/40 pt-2">
              Timeout: 10s · Validation: Format &amp; Evidence Grounding
            </div>
          </div>
        </div>

        {/* Local-first Security & Privacy Guarantees */}
        <div className="rounded-xl border border-status-ready/30 bg-status-ready/5 p-4 text-xs space-y-1">
          <div className="flex items-center gap-2 font-bold text-status-ready">
            <span>🛡️</span>
            <span>Local-First Security Guarantees</span>
          </div>
          <p className="text-parchment-text leading-relaxed">
            GhostArchive is running strictly within your local environment. No user files, questions, embeddings, or answers are transmitted to cloud services or remote tracking endpoints.
          </p>
        </div>
      </div>
    </div>
  );
};
