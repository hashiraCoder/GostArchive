import React, { useEffect, useState } from "react";
import { ApiException, type ApiError } from "../api/client";
import { askQuestion, type ChatResponse } from "../api/chat";
import { deleteDocument, listDocuments, uploadDocument, type DocumentItem } from "../api/documents";
import { searchDocuments, type SearchResult } from "../api/search";
import { summarizeArchive, type SummaryResponse } from "../api/summary";
import { DocumentLibrary } from "./DocumentLibrary";
import { ErrorBanner } from "./ErrorBanner";

export const ArchiveWorkspace: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState<ApiError | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [failedDelete, setFailedDelete] = useState<DocumentItem | null>(null);
  const [deleteError, setDeleteError] = useState<ApiError | null>(null);

  // Search state
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<ApiError | null>(null);

  // Ask / Q&A state
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [chatError, setChatError] = useState<ApiError | null>(null);

  // Summary state
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState<ApiError | null>(null);

  const loadDocuments = async () => {
    setDocumentsLoading(true);
    try {
      setDocuments((await listDocuments()).items);
      setDocumentsError(null);
    } catch (error) {
      setDocumentsError(
        error instanceof ApiException
          ? error.error
          : { code: "UNKNOWN_ERROR", message: "Could not load documents.", retryable: true }
      );
    } finally {
      setDocumentsLoading(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setDocumentsError(null);
    try {
      const response = await uploadDocument(file);
      setDocuments((current) => (response.duplicate ? current : [response.document, ...current]));
    } catch (error) {
      setDocumentsError(
        error instanceof ApiException
          ? error.error
          : { code: "UNKNOWN_ERROR", message: "Could not import document.", retryable: true }
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (document: DocumentItem) => {
    setDeletingId(document.id);
    setDeleteError(null);
    setFailedDelete(null);
    try {
      await deleteDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setSearchResults((current) => current.filter((item) => item.document_id !== document.id));
    } catch (error) {
      setFailedDelete(document);
      setDeleteError(
        error instanceof ApiException
          ? error.error
          : { code: "UNKNOWN_ERROR", message: "Could not delete document.", retryable: true }
      );
    } finally {
      setDeletingId(null);
    }
  };

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    setHasSearched(true);
    try {
      const res = await searchDocuments(query.trim());
      setSearchResults(res.items);
    } catch (error) {
      setSearchError(
        error instanceof ApiException
          ? error.error
          : { code: "UNKNOWN_ERROR", message: "Search failed.", retryable: true }
      );
    } finally {
      setSearching(false);
    }
  };

  const handleAsk = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!question.trim()) return;
    setAsking(true);
    setChatError(null);
    try {
      setChat(await askQuestion(question.trim()));
    } catch (error) {
      setChatError(
        error instanceof ApiException
          ? error.error
          : { code: "UNKNOWN_ERROR", message: "The archive could not answer this question.", retryable: true }
      );
    } finally {
      setAsking(false);
    }
  };

  const handleSummarize = async () => {
    setSummarizing(true);
    setSummaryError(null);
    try {
      const res = await summarizeArchive();
      setSummary(res);
    } catch (error) {
      setSummaryError(
        error instanceof ApiException
          ? error.error
          : { code: "UNKNOWN_ERROR", message: "Could not generate summary.", retryable: true }
      );
    } finally {
      setSummarizing(false);
    }
  };

  return (
    <div className="space-y-10">
      <DocumentLibrary
        documents={documents}
        loading={documentsLoading}
        error={documentsError}
        uploading={uploading}
        deletingId={deletingId}
        onUpload={handleUpload}
        onDelete={handleDelete}
        onRetry={() => void loadDocuments()}
      />

      {deleteError && (
        <ErrorBanner
          error={deleteError}
          onDismiss={() => {
            setDeleteError(null);
            setFailedDelete(null);
          }}
          onRetry={() => {
            if (failedDelete) void handleDelete(failedDelete);
          }}
        />
      )}

      {/* ── Summarize Capability ────────────────────────────────────── */}
      <section aria-labelledby="summary-heading" className="space-y-4 rounded border border-parchment-border bg-parchment-surface/50 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-parchment-muted">Archive Overview</p>
            <h2 id="summary-heading" className="font-serif text-2xl font-bold">Summarize Archive</h2>
          </div>
          <button
            type="button"
            onClick={() => void handleSummarize()}
            disabled={summarizing || documents.length === 0}
            className="rounded bg-parchment-accent px-4 py-2 text-sm font-medium text-parchment-surface disabled:opacity-50"
          >
            {summarizing ? "Analyzing archive…" : "Generate archive summary"}
          </button>
        </div>
        {summaryError && <ErrorBanner error={summaryError} onDismiss={() => setSummaryError(null)} />}
        {summary && (
          <article className="mt-4 space-y-3 rounded border border-parchment-border bg-parchment-surface p-4">
            <div className="text-xs text-parchment-muted italic">{summary.scope}</div>
            <div className="text-sm leading-relaxed whitespace-pre-line">{summary.summary}</div>
            {summary.limitations && summary.limitations.length > 0 && (
              <div className="mt-2 text-xs text-parchment-muted border-t border-parchment-border pt-2">
                <strong>Scope & Limitations:</strong>
                <ul className="list-disc pl-4 mt-1 space-y-1">
                  {summary.limitations.map((lim, idx) => (
                    <li key={idx}>{lim}</li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        )}
      </section>

      {/* ── Search Capability ────────────────────────────────────────── */}
      <section aria-labelledby="search-heading" className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-parchment-muted">Find by meaning & keyword</p>
          <h2 id="search-heading" className="font-serif text-2xl font-bold">Search the archive</h2>
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <label htmlFor="search-query" className="sr-only">Search query</label>
          <input
            id="search-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. drainage work before winter"
            className="min-w-0 flex-1 rounded border border-parchment-border bg-parchment-surface px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={searching}
            className="rounded border border-parchment-accent px-4 py-2 text-sm font-medium text-parchment-accent disabled:opacity-50"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        {searchError && <ErrorBanner error={searchError} onDismiss={() => setSearchError(null)} />}

        {!searching && hasSearched && searchResults.length === 0 && !searchError && (
          <p className="text-sm text-parchment-muted">
            No relevant passages were found in your archive. Try different wording or import documents that contain this topic.
          </p>
        )}

        <div className="space-y-3">
          {searchResults.map((result) => (
            <article key={result.chunk_id} className="rounded border border-parchment-border bg-parchment-surface p-4">
              <div className="flex justify-between items-center gap-3 text-xs text-parchment-muted">
                <div>
                  <strong>{result.filename}</strong>
                  {result.page_number != null && <span className="ml-2">(Page {result.page_number})</span>}
                </div>
                <span className="rounded bg-parchment-border/50 px-2 py-0.5 text-xs font-medium">
                  {result.relevance_label || "Relevant"}
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed">{result.text}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ── Ask / Q&A Capability ─────────────────────────────────────── */}
      <section aria-labelledby="ask-heading" className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-parchment-muted">Ask with evidence</p>
          <h2 id="ask-heading" className="font-serif text-2xl font-bold">Question your archive</h2>
        </div>
        <form onSubmit={handleAsk} className="space-y-2">
          <label htmlFor="archive-question" className="sr-only">Question</label>
          <textarea
            id="archive-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What does the archive say?"
            rows={3}
            className="w-full rounded border border-parchment-border bg-parchment-surface px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={asking}
            className="rounded bg-parchment-accent px-4 py-2 text-sm font-medium text-parchment-surface disabled:opacity-50"
          >
            {asking ? "Consulting evidence…" : "Ask archive"}
          </button>
        </form>

        {chatError && <ErrorBanner error={chatError} onDismiss={() => setChatError(null)} />}

        {chat && (
          <article className="rounded border border-parchment-border bg-parchment-surface p-5">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-serif text-lg font-bold">Answer</h3>
              <span className="text-xs text-parchment-muted">{chat.model}</span>
            </div>

            <p className="mt-3 leading-relaxed font-serif text-base">{chat.answer}</p>

            {chat.archive_context && (
              <div className="mt-3 text-sm text-parchment-muted">
                <strong>Archive details:</strong> {chat.archive_context}
              </div>
            )}

            {chat.limitations && chat.limitations.length > 0 && (
              <div className="mt-2 text-xs text-parchment-muted italic">
                {chat.limitations.join(" ")}
              </div>
            )}

            {chat.insufficient_evidence ? (
              <p className="mt-4 rounded bg-status-degraded/10 p-3 text-sm text-status-degraded">
                Insufficient evidence in the retrieved archive passages.
              </p>
            ) : (
              <div className="mt-5 space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-widest text-parchment-muted">Sources</h4>
                {chat.citations.map((citation) => (
                  <details key={citation.chunk_id} open className="rounded border border-parchment-border p-3">
                    <summary className="cursor-pointer text-sm font-medium flex items-center justify-between">
                      <span>{citation.document_title || citation.filename}</span>
                      <span className="text-xs text-parchment-muted">{citation.evidence_type || "Direct evidence"}</span>
                    </summary>
                    <p className="mt-2 border-l-2 border-parchment-accent pl-3 text-sm leading-relaxed">
                      {citation.excerpt}
                    </p>
                  </details>
                ))}
              </div>
            )}
          </article>
        )}
      </section>
    </div>
  );
};
