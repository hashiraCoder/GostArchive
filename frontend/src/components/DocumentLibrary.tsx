import React, { useRef, useState } from "react";
import type { ApiError } from "../api/client";
import type { DocumentItem } from "../api/documents";

interface DocumentLibraryProps {
  documents: DocumentItem[];
  loading: boolean;
  error: ApiError | null;
  uploading: boolean;
  deletingId: string | null;
  onUpload: (file: File) => void;
  onDelete: (document: DocumentItem) => void;
  onRetry: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  loading,
  error,
  uploading,
  deletingId,
  onUpload,
  onDelete,
  onRetry,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [confirming, setConfirming] = useState<DocumentItem | null>(null);

  const handleFile = (file: File | undefined) => {
    if (file) onUpload(file);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <section aria-labelledby="archive-heading" className="space-y-4">
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
            accept=".txt,.md,text/plain,text/markdown"
            onChange={(event) => handleFile(event.target.files?.[0])}
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="rounded bg-parchment-accent px-4 py-2 text-sm font-medium text-parchment-surface disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? "Importing…" : "Import document"}
          </button>
        </div>
      </div>

      {error && (
        <div role="alert" className="rounded border border-status-unavailable/30 bg-red-50 p-3 text-sm text-status-unavailable">
          <strong>{error.code}</strong>
          <p>{error.message}</p>
          {error.retryable && <button type="button" onClick={onRetry} className="mt-2 underline">Try again</button>}
        </div>
      )}

      {loading ? (
        <div aria-label="Loading documents" className="rounded border border-parchment-border bg-parchment-surface p-8 text-center text-parchment-muted">
          Loading your archive…
        </div>
      ) : documents.length === 0 && !error ? (
        <div className="rounded border-2 border-dashed border-parchment-border bg-parchment-surface/50 p-8 text-center">
          <h3 className="font-serif text-lg font-semibold">No documents yet</h3>
          <p className="mt-1 text-sm text-parchment-muted">Import a .txt or .md file to begin exploring your records.</p>
        </div>
      ) : (
        <ul className="divide-y divide-parchment-border rounded border border-parchment-border bg-parchment-surface">
          {documents.map((document) => (
            <li key={document.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="truncate font-medium">{document.filename}</p>
                <p className="text-xs text-parchment-muted">
                  {document.file_type.toUpperCase()} · {formatBytes(document.byte_size)} · {document.chunk_count} chunks
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs uppercase tracking-wide text-status-ready">{document.status}</span>
                <button type="button" onClick={() => setConfirming(document)} disabled={deletingId === document.id} className="text-sm text-status-unavailable underline disabled:opacity-50">
                  {deletingId === document.id ? "Deleting…" : "Delete"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {confirming && (
        <div role="dialog" aria-modal="true" aria-labelledby="delete-title" className="fixed inset-0 z-20 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded border border-parchment-border bg-parchment-surface p-6 shadow-xl">
            <h3 id="delete-title" className="font-serif text-lg font-bold">Delete {confirming.filename}?</h3>
            <p className="mt-2 text-sm text-parchment-muted">This removes the source file, metadata, chunks, and search vectors.</p>
            <div className="mt-5 flex justify-end gap-3">
              <button type="button" onClick={() => setConfirming(null)} className="rounded border border-parchment-border px-3 py-2 text-sm">Cancel</button>
              <button type="button" onClick={() => { onDelete(confirming); setConfirming(null); }} className="rounded bg-status-unavailable px-3 py-2 text-sm text-white">Delete document</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
