import React from "react";
import type { ApiError } from "../../api/client";
import type { DocumentItem } from "../../api/documents";
import type { ConversationSummary } from "../../api/conversations";
import type { ReadyResponse } from "../../api/health";
import type { SummaryResponse } from "../../api/summary";
import { ErrorBanner } from "../ErrorBanner";

interface OverviewViewProps {
  documents: DocumentItem[];
  conversations: ConversationSummary[];
  readyStatus: ReadyResponse | null;
  onNavigate: (tab: "overview" | "documents" | "ask" | "conversations" | "status") => void;
  onSummarize: () => void;
  summary: SummaryResponse | null;
  summarizing: boolean;
  summaryError: ApiError | null;
  onDismissSummaryError: () => void;
  isOllamaOffline: boolean;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  documents,
  conversations,
  readyStatus,
  onNavigate,
  onSummarize,
  summary,
  summarizing,
  summaryError,
  onDismissSummaryError,
  isOllamaOffline,
}) => {
  const readyDocs = documents.filter((d) => d.status.toLowerCase() === "ready");
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const recentDocs = documents.slice(0, 5);

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    const kb = (bytes / 1024).toFixed(1);
    return `${kb} KB`;
  };

  const isAllReady = readyStatus?.overall === "ready";

  return (
    <div className="space-y-6">
      {/* ── Welcome Hero ─────────────────────────────────────────── */}
      <div className="rounded-xl border border-parchment-border bg-parchment-surface p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-2xl space-y-2">
          <p className="text-xs font-bold uppercase tracking-wider text-parchment-accent">
            Personal Knowledge Repository
          </p>
          <h2 className="font-serif text-2xl md:text-3xl font-bold text-parchment-text">
            Welcome to your memory archive
          </h2>
          <p className="text-sm text-parchment-muted leading-relaxed">
            GhostArchive preserves your personal notes, technical documents, and records with zero cloud exposure.
            Every query is resolved strictly through local semantic retrieval and cross-validated with SQLite citations.
          </p>
        </div>
        <div className="shrink-0 flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            onClick={() => onNavigate("ask")}
            className="px-5 py-2.5 rounded-lg bg-parchment-accent text-parchment-surface font-semibold text-sm hover:bg-parchment-accent-hover transition shadow-sm"
          >
            Ask Archive
          </button>
          <button
            type="button"
            onClick={() => onNavigate("documents")}
            className="px-5 py-2.5 rounded-lg border border-parchment-border bg-parchment-surface text-parchment-text font-semibold text-sm hover:bg-parchment-sidebar transition"
          >
            Manage Documents
          </button>
        </div>
      </div>

      {/* ── Metric Cards ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-parchment-border bg-parchment-surface p-4 shadow-sm">
          <p className="text-xs font-medium text-parchment-muted">Total Documents</p>
          <p className="text-2xl font-serif font-bold text-parchment-text mt-1">
            {documents.length}
          </p>
          <p className="text-[11px] text-status-ready mt-1 font-medium">
            {readyDocs.length} Ready in SQLite
          </p>
        </div>

        <div className="rounded-xl border border-parchment-border bg-parchment-surface p-4 shadow-sm">
          <p className="text-xs font-medium text-parchment-muted">Indexed Passages</p>
          <p className="text-2xl font-serif font-bold text-parchment-text mt-1">
            {totalChunks}
          </p>
          <p className="text-[11px] text-parchment-muted mt-1 font-mono">
            Chroma HNSW + FTS5
          </p>
        </div>

        <div className="rounded-xl border border-parchment-border bg-parchment-surface p-4 shadow-sm">
          <p className="text-xs font-medium text-parchment-muted">Saved Discussions</p>
          <p className="text-2xl font-serif font-bold text-parchment-text mt-1">
            {conversations.length}
          </p>
          <p className="text-[11px] text-parchment-muted mt-1">
            Multi-turn persisted
          </p>
        </div>

        <div className="rounded-xl border border-parchment-border bg-parchment-surface p-4 shadow-sm">
          <p className="text-xs font-medium text-parchment-muted">AI Privacy</p>
          <p className="text-2xl font-serif font-bold text-status-ready mt-1">
            100%
          </p>
          <p className="text-[11px] text-parchment-muted mt-1">
            {isAllReady ? "Local Ollama ready" : "Local loopback"}
          </p>
        </div>
      </div>

      {/* ── Recent Documents Section ──────────────────────────────── */}
      <div className="rounded-xl border border-parchment-border bg-parchment-surface p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between border-b border-parchment-border pb-3">
          <h3 className="font-serif font-bold text-base text-parchment-text">Recent Archive Documents</h3>
          <button
            type="button"
            onClick={() => onNavigate("documents")}
            className="text-xs font-semibold text-parchment-accent hover:underline"
          >
            View All Documents ({documents.length}) →
          </button>
        </div>

        {recentDocs.length === 0 ? (
          <div className="text-center py-6 text-xs text-parchment-muted">
            No documents in archive yet.{" "}
            <button
              type="button"
              onClick={() => onNavigate("documents")}
              className="text-parchment-accent underline font-semibold"
            >
              Upload your first document
            </button>
          </div>
        ) : (
          <div className="divide-y divide-parchment-border/60 text-xs">
            {recentDocs.map((doc) => (
              <div key={doc.id} className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="p-1.5 rounded bg-parchment-sidebar text-parchment-accent font-mono text-[10px] uppercase font-bold">
                    {doc.file_type}
                  </span>
                  <span className="font-medium text-parchment-text">{doc.filename}</span>
                  <span className="text-parchment-muted">
                    ({doc.chunk_count} chunk{doc.chunk_count === 1 ? "" : "s"} · {formatBytes(doc.byte_size)})
                  </span>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                    doc.status.toLowerCase() === "ready"
                      ? "text-status-ready bg-status-ready/10 border-status-ready/20"
                      : "text-status-degraded bg-status-degraded/10 border-status-degraded/20"
                  }`}
                >
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Quick Archive Synthesis ───────────────────────────────── */}
      <div className="rounded-xl border border-parchment-border bg-parchment-surface p-5 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-parchment-border pb-3">
          <div>
            <h3 className="font-serif font-bold text-base text-parchment-text">Corpus Synthesis</h3>
            <p className="text-xs text-parchment-muted">
              Generate a high-level briefing summarizing key themes, decisions, and records across your archive.
            </p>
          </div>
          <button
            type="button"
            onClick={onSummarize}
            disabled={summarizing || isOllamaOffline || documents.length === 0}
            className="px-4 py-2 rounded-lg bg-parchment-accent text-parchment-surface font-semibold text-xs hover:bg-parchment-accent-hover transition disabled:opacity-50 shrink-0"
          >
            {summarizing ? "Generating summary…" : "Generate Archive Summary"}
          </button>
        </div>

        {summaryError && <ErrorBanner error={summaryError} onDismiss={onDismissSummaryError} />}

        {summary && (
          <article className="pt-2 space-y-2">
            <h4 className="font-serif text-sm font-bold text-parchment-text">Executive Briefing</h4>
            <p className="text-xs leading-relaxed text-parchment-text font-serif whitespace-pre-line border-l-2 border-parchment-accent pl-3 py-1">
              {summary.summary}
            </p>
            {summary.limitations && summary.limitations.length > 0 && (
              <div className="pt-2 text-[11px] text-parchment-muted">
                <span className="font-semibold">Scope &amp; Limitations:</span>
                <ul className="mt-1 list-disc pl-4 space-y-0.5">
                  {summary.limitations.map((lim, idx) => (
                    <li key={idx}>{lim}</li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        )}
      </div>
    </div>
  );
};
