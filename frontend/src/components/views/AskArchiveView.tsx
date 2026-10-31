import React from "react";
import type { ApiError } from "../../api/client";
import type { DocumentItem } from "../../api/documents";
import type { SearchResult } from "../../api/search";
import type {
  ConversationSummary,
  ConversationDetailResponse,
} from "../../api/conversations";
import { ConversationSidebar } from "../ConversationSidebar";
import { ConversationThread } from "../ConversationThread";
import { ErrorBanner } from "../ErrorBanner";
import { EmptyState } from "../EmptyState";

interface AskArchiveViewProps {
  documents: DocumentItem[];
  selectedScope: string;
  scopeLabel: string;
  onScopeChange: (scope: string) => void;
  // Search state
  query: string;
  setQuery: (q: string) => void;
  searchResults: SearchResult[];
  hasSearched: boolean;
  searching: boolean;
  searchError: ApiError | null;
  onSearch: (e: React.FormEvent) => Promise<void>;
  onDismissSearchError: () => void;
  // Conversations state
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  activeConversation: ConversationDetailResponse | null;
  conversationsLoading: boolean;
  chatError: ApiError | null;
  asking: boolean;
  onSelectConversation: (id: string) => Promise<void>;
  onCreateConversation: () => Promise<void>;
  onRenameConversation: (id: string, newTitle: string) => Promise<void>;
  onDeleteConversation: (id: string) => Promise<void>;
  onSendMessage: (question: string) => Promise<void>;
  onRetryMessage: (clientTurnId: string, question: string) => Promise<void>;
  onDismissChatError: () => void;
  // Ollama status
  isOllamaOffline: boolean;
  isOllamaDaemonOffline: boolean;
  isModelMissing: boolean;
}

export const AskArchiveView: React.FC<AskArchiveViewProps> = ({
  documents,
  selectedScope,
  scopeLabel,
  onScopeChange,
  query,
  setQuery,
  searchResults,
  hasSearched,
  searching,
  searchError,
  onSearch,
  onDismissSearchError,
  conversations,
  activeConversationId,
  activeConversation,
  conversationsLoading,
  chatError,
  asking,
  onSelectConversation,
  onCreateConversation,
  onRenameConversation,
  onDeleteConversation,
  onSendMessage,
  onRetryMessage,
  onDismissChatError,
  isOllamaOffline,
  isOllamaDaemonOffline,
  isModelMissing,
}) => {
  const readyDocuments = documents.filter((d) => d.status.toLowerCase() === "ready");

  return (
    <div className="space-y-8">
      {/* ── Scope Selection Card ────────────────────────────────────── */}
      <section
        aria-labelledby="scope-heading"
        className="rounded-xl border border-parchment-border bg-parchment-surface p-5 shadow-sm space-y-4"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 id="scope-heading" className="font-serif text-lg font-bold text-parchment-text">
              Archive Scope Selection
            </h2>
            <p className="text-xs text-parchment-muted mt-0.5">
              Control the exact boundary for search and evidence retrieval across your archive.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="scope-select" className="text-xs font-semibold text-parchment-text shrink-0">
              Active Scope:
            </label>
            <select
              id="scope-select"
              value={selectedScope}
              onChange={(e) => onScopeChange(e.target.value)}
              className="rounded-lg border border-parchment-border bg-parchment-bg px-3 py-1.5 text-xs text-parchment-text font-medium focus:outline-none focus:ring-1 focus:ring-parchment-accent"
            >
              <option value="all">
                Entire Archive ({readyDocuments.length} ready document{readyDocuments.length === 1 ? "" : "s"})
              </option>
              {readyDocuments.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  📄 {doc.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-parchment-muted border-t border-parchment-border/60 pt-3">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Current Retrieval Target:</span>
          <span className="rounded bg-parchment-sidebar px-2 py-0.5 text-parchment-text font-medium border border-parchment-border">
            {scopeLabel}
          </span>
        </div>
      </section>

      {/* ── Ask / Q&A Capability with Persistent Discussions ───────────── */}
      <section aria-labelledby="ask-heading" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-parchment-border pb-3">
          <div>
            <p className="text-xs uppercase tracking-widest text-parchment-muted font-bold">Ask with evidence</p>
            <h2 id="ask-heading" className="font-serif text-2xl font-bold text-parchment-text">
              Question your archive
            </h2>
          </div>
          <span className="text-xs text-parchment-muted">
            Scope: <strong className="text-parchment-text">{scopeLabel}</strong>
          </span>
        </div>

        {chatError && <ErrorBanner error={chatError} onDismiss={onDismissChatError} />}

        <div className="flex flex-col md:flex-row gap-5 items-stretch">
          <ConversationSidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={onSelectConversation}
            onCreateConversation={onCreateConversation}
            onRenameConversation={onRenameConversation}
            onDeleteConversation={onDeleteConversation}
            loading={conversationsLoading}
          />
          <ConversationThread
            conversation={activeConversation}
            activeScope={selectedScope}
            scopeLabel={scopeLabel}
            onSendMessage={onSendMessage}
            onRetryMessage={onRetryMessage}
            isOllamaOffline={isOllamaOffline}
            isOllamaDaemonOffline={isOllamaDaemonOffline}
            isModelMissing={isModelMissing}
            sendingQuestion={asking}
          />
        </div>
      </section>

      {/* ── Search Capability Accordion / Section ──────────────────────── */}
      <section aria-labelledby="search-heading" className="space-y-4 border-t border-parchment-border pt-8">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
          <div>
            <p className="text-xs uppercase tracking-widest text-parchment-muted font-bold">Semantic &amp; Keyword</p>
            <h2 id="search-heading" className="font-serif text-xl font-bold text-parchment-text">
              Search Documents
            </h2>
          </div>
          <span className="text-xs text-parchment-muted">
            Target: <strong className="text-parchment-text">{scopeLabel}</strong>
          </span>
        </div>

        <form onSubmit={onSearch} className="flex gap-2">
          <label htmlFor="search-input" className="sr-only">
            Search query
          </label>
          <input
            id="search-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={`Search across ${selectedScope === "all" ? "entire archive" : scopeLabel}…`}
            className="flex-1 rounded-lg border border-parchment-border bg-parchment-surface px-3 py-2 text-sm text-parchment-text placeholder:text-parchment-muted focus:outline-none focus:ring-1 focus:ring-parchment-accent"
          />
          <button
            type="submit"
            disabled={searching}
            className="rounded-lg bg-parchment-accent px-4 py-2 text-sm font-medium text-parchment-surface hover:bg-parchment-accent-hover transition disabled:opacity-50"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        {searchError && <ErrorBanner error={searchError} onDismiss={onDismissSearchError} />}

        {hasSearched && searchResults.length === 0 && !searching && (
          <EmptyState
            title="No relevant passages found"
            message={`No document passages matched your search query in ${selectedScope === "all" ? "the archive" : scopeLabel}.`}
          />
        )}

        <div className="space-y-3">
          {searchResults.map((result) => (
            <article key={result.chunk_id} className="rounded-xl border border-parchment-border bg-parchment-surface p-4 shadow-sm">
              <div className="flex justify-between items-center gap-3 text-xs text-parchment-muted">
                <div>
                  <strong className="text-parchment-text">{result.filename}</strong>
                  {result.page_number != null && <span className="ml-2">(Page {result.page_number})</span>}
                </div>
                <span
                  className={`rounded px-2 py-0.5 text-xs font-medium border ${
                    result.relevance_label === "High match"
                      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                      : result.relevance_label === "Medium match"
                      ? "border-blue-200 bg-blue-50 text-blue-800"
                      : "border-parchment-border bg-parchment-border/40 text-parchment-muted"
                  }`}
                >
                  {result.relevance_label || "Relevant"}
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-parchment-text">{result.text}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
};
