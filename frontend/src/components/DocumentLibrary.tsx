import React, { useRef, useState, useMemo, useEffect, useCallback } from "react";
import type { ApiError } from "../api/client";
import {
  type DocumentItem,
  uploadDocument,
  bulkDeleteDocuments,
  type BulkDeleteResponse,
} from "../api/documents";
import { ApiException } from "../api/client";
import { EmptyState } from "./EmptyState";

interface DocumentLibraryProps {
  documents: DocumentItem[];
  loading: boolean;
  error: ApiError | null;
  uploading?: boolean;
  deletingId: string | null;
  onUpload?: (file: File) => void;
  onDocumentAdded?: (document: DocumentItem, duplicate: boolean) => void;
  onDelete: (document: DocumentItem) => void;
  onBulkDeleteSuccess?: (deletedIds: string[]) => void;
  onRetry: () => void;
}

export interface UploadQueueItem {
  id: string;
  file: File;
  status: "queued" | "uploading" | "ready" | "duplicate" | "failed";
  error?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function formatDate(isoString: string): string {
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

function renderStatusBadge(status: string, errorCode?: string | null) {
  const norm = status.toLowerCase();
  if (norm === "ready") {
    return (
      <span className="inline-flex items-center rounded border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
        ready
      </span>
    );
  }
  if (norm === "processing") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-600" />
        indexing
      </span>
    );
  }
  if (norm === "deleting") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded border border-gray-300 bg-gray-50 px-2 py-0.5 text-xs font-medium text-gray-700">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gray-500" />
        deleting
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1 rounded border border-red-300 bg-red-50 px-2 py-0.5 text-xs font-medium text-red-800"
      title={errorCode ? `Error: ${errorCode}` : undefined}
    >
      {status}{errorCode ? `: ${errorCode}` : ""}
    </span>
  );
}

const PAGE_SIZE = 10;

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  loading,
  error,
  uploading: externalUploading = false,
  deletingId,
  onUpload,
  onDocumentAdded,
  onDelete,
  onBulkDeleteSuccess,
  onRetry,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [confirmingSingle, setConfirmingSingle] = useState<DocumentItem | null>(null);
  const [confirmingBulk, setConfirmingBulk] = useState(false);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);
  const [bulkDeleteFeedback, setBulkDeleteFeedback] = useState<string | null>(null);

  // Drag and drop state
  const [isDragging, setIsDragging] = useState(false);

  // Multi-file upload queue
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);

  // Management: search, filters, pagination, selection
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Filter documents client-side for instant responsive interaction
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = doc.filename.toLowerCase().includes(q);
        if (!matchesName) return false;
      }
      if (statusFilter !== "all" && doc.status.toLowerCase() !== statusFilter.toLowerCase()) {
        return false;
      }
      if (typeFilter !== "all" && doc.file_type.toLowerCase() !== typeFilter.toLowerCase()) {
        return false;
      }
      return true;
    });
  }, [documents, searchQuery, statusFilter, typeFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredDocuments.length / PAGE_SIZE));
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const pagedDocuments = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredDocuments.slice(start, start + PAGE_SIZE);
  }, [filteredDocuments, currentPage]);

  // Queue runner: processes one file at a time without loading all into memory
  const processNextInQueue = useCallback(async () => {
    if (isProcessingQueue) return;

    // Find first queued item
    const nextItem = uploadQueue.find((item) => item.status === "queued");
    if (!nextItem) return;

    setIsProcessingQueue(true);
    setUploadQueue((current) =>
      current.map((item) =>
        item.id === nextItem.id ? { ...item, status: "uploading" } : item
      )
    );

    try {
      const response = await uploadDocument(nextItem.file);
      setUploadQueue((current) =>
        current.map((item) =>
          item.id === nextItem.id
            ? { ...item, status: response.duplicate ? "duplicate" : "ready" }
            : item
        )
      );
      if (onDocumentAdded) {
        onDocumentAdded(response.document, response.duplicate);
      }
    } catch (err) {
      const errorMsg =
        err instanceof ApiException
          ? err.error.message
          : err instanceof Error
          ? err.message
          : "Failed to upload file.";
      setUploadQueue((current) =>
        current.map((item) =>
          item.id === nextItem.id ? { ...item, status: "failed", error: errorMsg } : item
        )
      );
    } finally {
      setIsProcessingQueue(false);
    }
  }, [isProcessingQueue, uploadQueue, onUpload, onDocumentAdded]);

  useEffect(() => {
    const hasQueued = uploadQueue.some((item) => item.status === "queued");
    if (hasQueued && !isProcessingQueue) {
      void processNextInQueue();
    }
  }, [uploadQueue, isProcessingQueue, processNextInQueue]);

  // Handle newly selected or dropped files
  const handleFiles = (files: FileList | File[] | null) => {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files);

    const newQueueItems: UploadQueueItem[] = fileArray.map((file) => ({
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      file,
      status: "queued",
    }));

    setUploadQueue((current) => [...current, ...newQueueItems]);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleRetryFailed = (itemId: string) => {
    setUploadQueue((current) =>
      current.map((item) =>
        item.id === itemId ? { ...item, status: "queued", error: undefined } : item
      )
    );
  };

  const handleClearFinished = () => {
    setUploadQueue((current) =>
      current.filter((item) => item.status === "queued" || item.status === "uploading")
    );
  };

  // Selection handlers
  const handleToggleSelectAllOnPage = () => {
    const pageIds = pagedDocuments.map((d) => d.id);
    const allSelected = pageIds.every((id) => selectedIds.has(id));

    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        pageIds.forEach((id) => next.delete(id));
      } else {
        pageIds.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  const handleToggleSelectDoc = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Bulk deletion execution
  const executeBulkDelete = async () => {
    const idsToDelete = Array.from(selectedIds);
    if (idsToDelete.length === 0) return;

    setIsBulkDeleting(true);
    setBulkDeleteFeedback(null);
    try {
      const response: BulkDeleteResponse = await bulkDeleteDocuments(idsToDelete);
      const successfulIds = response.results.filter((r) => r.success).map((r) => r.id);

      setSelectedIds((prev) => {
        const next = new Set(prev);
        successfulIds.forEach((id) => next.delete(id));
        return next;
      });

      if (onBulkDeleteSuccess) {
        onBulkDeleteSuccess(successfulIds);
      }

      setBulkDeleteFeedback(
        `Bulk delete finished: ${response.total_deleted} of ${idsToDelete.length} document(s) deleted.`
      );
    } catch (err) {
      setBulkDeleteFeedback("Bulk delete failed. Please try again.");
    } finally {
      setIsBulkDeleting(false);
      setConfirmingBulk(false);
    }
  };

  const hasProcessingDocs = documents.some((d) => d.status.toLowerCase() === "processing");
  const allOnPageSelected =
    pagedDocuments.length > 0 && pagedDocuments.every((d) => selectedIds.has(d.id));

  return (
    <section aria-labelledby="archive-heading" className="space-y-6">
      {/* Header and Import action */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-parchment-muted">Your collection</p>
          <h2 id="archive-heading" className="font-serif text-2xl font-bold">Archive documents</h2>
        </div>
        <div>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            multiple
            accept=".txt,.md,text/plain,text/markdown"
            onChange={(event) => handleFiles(event.target.files)}
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={externalUploading || isProcessingQueue}
            className="rounded bg-parchment-accent px-4 py-2 text-sm font-medium text-parchment-surface disabled:cursor-not-allowed disabled:opacity-60 shadow-sm transition hover:opacity-90"
          >
            {externalUploading || isProcessingQueue ? "Importing files…" : "Import documents"}
          </button>
        </div>
      </div>

      {/* Drag & Drop Import Dropzone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition ${
          isDragging
            ? "border-parchment-accent bg-parchment-accent/10"
            : "border-parchment-border bg-parchment-surface/40 hover:bg-parchment-surface/80"
        }`}
      >
        <div className="flex flex-col items-center gap-1.5 text-sm text-parchment-muted">
          <svg className="h-6 w-6 text-parchment-accent/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="font-medium text-parchment-text">
            Drop .txt or .md files here, or <span className="text-parchment-accent underline">browse</span>
          </p>
          <p className="text-xs text-parchment-muted">Select multiple files to upload in a controlled batch</p>
        </div>
      </div>

      {/* Multi-file Upload Queue Progress Panel */}
      {uploadQueue.length > 0 && (
        <div className="rounded border border-parchment-border bg-parchment-surface p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold uppercase tracking-wider text-parchment-muted">
              Batch Upload Queue ({uploadQueue.filter((i) => i.status === "ready" || i.status === "duplicate").length}/{uploadQueue.length} done)
            </span>
            <button
              type="button"
              onClick={handleClearFinished}
              disabled={isProcessingQueue}
              className="text-parchment-accent underline hover:opacity-80 disabled:opacity-50"
            >
              Clear completed
            </button>
          </div>

          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {uploadQueue.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 text-xs p-2 rounded border border-parchment-border/60 bg-parchment-bg/50"
              >
                <div className="min-w-0 flex-1 truncate">
                  <span className="font-medium text-parchment-text">{item.file.name}</span>
                  <span className="text-parchment-muted ml-2">({formatBytes(item.file.size)})</span>
                </div>

                <div className="flex items-center gap-2">
                  {item.status === "queued" && (
                    <span className="text-parchment-muted">Queued…</span>
                  )}
                  {item.status === "uploading" && (
                    <span className="inline-flex items-center gap-1 text-amber-700">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-600" />
                      Indexing…
                    </span>
                  )}
                  {item.status === "ready" && (
                    <span className="inline-flex items-center gap-1 text-emerald-800 font-medium">
                      ✓ Imported
                    </span>
                  )}
                  {item.status === "duplicate" && (
                    <span className="inline-flex items-center gap-1 text-blue-800 font-medium">
                      ℹ Duplicate (Preserved)
                    </span>
                  )}
                  {item.status === "failed" && (
                    <div className="flex items-center gap-2">
                      <span className="text-red-700 truncate max-w-xs" title={item.error}>
                        ✕ {item.error || "Failed"}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRetryFailed(item.id)}
                        className="underline text-parchment-accent font-medium hover:opacity-80"
                      >
                        Retry
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing State Guidance */}
      {hasProcessingDocs && (
        <div role="status" className="rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-amber-600" />
          <span>
            <strong>Indexing in progress:</strong> One or more documents are currently being chunked and indexed into the local vector store. Search results may be partial until status is ready.
          </span>
        </div>
      )}

      {/* Global Error Banner */}
      {error && (
        <div role="alert" className="rounded border border-status-unavailable/30 bg-red-50 p-3 text-sm text-status-unavailable">
          <strong>{error.code}</strong>
          <p>{error.message}</p>
          {error.retryable && (
            <button type="button" onClick={onRetry} className="mt-2 underline">
              Try again
            </button>
          )}
        </div>
      )}

      {/* Bulk Delete Feedback */}
      {bulkDeleteFeedback && (
        <div className="rounded border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 flex items-center justify-between">
          <span>{bulkDeleteFeedback}</span>
          <button
            type="button"
            onClick={() => setBulkDeleteFeedback(null)}
            className="text-xs text-emerald-900 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Document Management Bar: Search, Filters, Selection Actions */}
      <div className="flex flex-col gap-3 rounded border border-parchment-border bg-parchment-surface p-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          {/* Filename Search */}
          <div className="min-w-[180px] flex-1">
            <label htmlFor="doc-search" className="sr-only">Search documents by filename</label>
            <input
              id="doc-search"
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Filter by filename…"
              className="w-full rounded border border-parchment-border bg-parchment-bg px-3 py-1.5 text-xs text-parchment-text"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label htmlFor="status-filter" className="sr-only">Filter by status</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="rounded border border-parchment-border bg-parchment-bg px-2.5 py-1.5 text-xs text-parchment-text"
            >
              <option value="all">All statuses</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="error">Error</option>
            </select>
          </div>

          {/* File Type Filter */}
          <div>
            <label htmlFor="type-filter" className="sr-only">Filter by file type</label>
            <select
              id="type-filter"
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="rounded border border-parchment-border bg-parchment-bg px-2.5 py-1.5 text-xs text-parchment-text"
            >
              <option value="all">All types</option>
              <option value="txt">.txt</option>
              <option value="md">.md</option>
            </select>
          </div>
        </div>

        {/* Bulk Action Controls */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 border-t border-parchment-border pt-2 sm:border-t-0 sm:pt-0">
            <span className="text-xs font-medium text-parchment-accent">
              {selectedIds.size} selected
            </span>
            <button
              type="button"
              onClick={() => setConfirmingBulk(true)}
              disabled={isBulkDeleting}
              className="rounded bg-status-unavailable px-3 py-1 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
            >
              {isBulkDeleting ? "Deleting…" : "Delete selected"}
            </button>
          </div>
        )}
      </div>

      {/* Document Table / List */}
      {loading ? (
        <div aria-label="Loading documents" className="rounded border border-parchment-border bg-parchment-surface p-8 text-center text-parchment-muted">
          Loading your archive…
        </div>
      ) : documents.length === 0 && !error ? (
        <EmptyState
          title="No documents yet"
          message="Import .txt or .md files to begin exploring your records."
          actionText="Import document"
          onAction={() => inputRef.current?.click()}
        />
      ) : filteredDocuments.length === 0 ? (
        <div className="rounded border border-parchment-border bg-parchment-surface p-8 text-center text-sm text-parchment-muted space-y-2">
          <p>No documents match your filter criteria.</p>
          <button
            type="button"
            onClick={() => {
              setSearchQuery("");
              setStatusFilter("all");
              setTypeFilter("all");
            }}
            className="text-xs text-parchment-accent underline"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="rounded border border-parchment-border bg-parchment-surface overflow-hidden">
          {/* Table Header with Master Checkbox */}
          <div className="flex items-center justify-between border-b border-parchment-border bg-parchment-surface/60 px-4 py-2.5 text-xs font-semibold text-parchment-muted">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={allOnPageSelected}
                onChange={handleToggleSelectAllOnPage}
                aria-label="Select all documents on current page"
                className="h-4 w-4 rounded border-parchment-border text-parchment-accent focus:ring-parchment-accent"
              />
              <span>Document</span>
            </div>
            <span>Status & Actions</span>
          </div>

          <ul className="divide-y divide-parchment-border">
            {pagedDocuments.map((document) => {
              const isSelected = selectedIds.has(document.id);
              return (
                <li
                  key={document.id}
                  className={`flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between transition ${
                    isSelected ? "bg-parchment-accent/5" : ""
                  }`}
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleSelectDoc(document.id)}
                      aria-label={`Select ${document.filename}`}
                      className="mt-1 h-4 w-4 rounded border-parchment-border text-parchment-accent focus:ring-parchment-accent"
                    />
                    <div className="min-w-0">
                      <p className="truncate font-medium text-parchment-text">{document.filename}</p>
                      <p className="text-xs text-parchment-muted">
                        {document.file_type.toUpperCase()} · {formatBytes(document.byte_size)} · {document.chunk_count} chunks
                        {document.created_at && formatDate(document.created_at) && (
                          <span className="ml-2">· Added {formatDate(document.created_at)}</span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    {renderStatusBadge(document.status, document.error_code)}
                    <button
                      type="button"
                      onClick={() => setConfirmingSingle(document)}
                      disabled={deletingId !== null || isBulkDeleting}
                      className="text-xs text-status-unavailable underline disabled:opacity-50 hover:opacity-80"
                    >
                      {deletingId === document.id ? "Deleting…" : "Delete"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-parchment-border bg-parchment-surface/40 px-4 py-3 text-xs text-parchment-muted">
              <div>
                Showing {(currentPage - 1) * PAGE_SIZE + 1}–
                {Math.min(currentPage * PAGE_SIZE, filteredDocuments.length)} of {filteredDocuments.length}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="rounded border border-parchment-border px-2.5 py-1 disabled:opacity-40 hover:bg-parchment-surface"
                >
                  Previous
                </button>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="rounded border border-parchment-border px-2.5 py-1 disabled:opacity-40 hover:bg-parchment-surface"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Single Document Delete Confirmation Dialog */}
      {confirmingSingle && (
        <div role="dialog" aria-modal="true" aria-labelledby="delete-title" className="fixed inset-0 z-20 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded border border-parchment-border bg-parchment-surface p-6 shadow-xl">
            <h3 id="delete-title" className="font-serif text-lg font-bold">Delete {confirmingSingle.filename}?</h3>
            <p className="mt-2 text-sm text-parchment-muted">This removes the source file, metadata, chunks, and search vectors.</p>
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setConfirmingSingle(null)}
                disabled={deletingId !== null}
                className="rounded border border-parchment-border px-3 py-2 text-sm disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deletingId !== null}
                onClick={() => {
                  onDelete(confirmingSingle);
                  setConfirmingSingle(null);
                }}
                className="rounded bg-status-unavailable px-3 py-2 text-sm text-white disabled:opacity-50"
              >
                {deletingId === confirmingSingle.id ? "Deleting…" : "Delete document"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Confirmation Dialog */}
      {confirmingBulk && (
        <div role="dialog" aria-modal="true" aria-labelledby="bulk-delete-title" className="fixed inset-0 z-20 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded border border-parchment-border bg-parchment-surface p-6 shadow-xl">
            <h3 id="bulk-delete-title" className="font-serif text-lg font-bold">
              Delete {selectedIds.size} selected documents?
            </h3>
            <p className="mt-2 text-sm text-parchment-muted">
              This permanently removes all source files, SQLite records, chunks, and vector search embeddings for the selected documents. This action cannot be undone.
            </p>
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setConfirmingBulk(false)}
                disabled={isBulkDeleting}
                className="rounded border border-parchment-border px-3 py-2 text-sm disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isBulkDeleting}
                onClick={executeBulkDelete}
                className="rounded bg-status-unavailable px-3 py-2 text-sm text-white disabled:opacity-50"
              >
                {isBulkDeleting ? "Deleting…" : `Delete ${selectedIds.size} documents`}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
