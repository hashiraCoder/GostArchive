import React from "react";
import type { ApiError } from "../../api/client";
import type { DocumentItem } from "../../api/documents";
import { DocumentLibrary } from "../DocumentLibrary";
import { ErrorBanner } from "../ErrorBanner";

interface DocumentsViewProps {
  documents: DocumentItem[];
  loading: boolean;
  error: ApiError | null;
  uploading: boolean;
  deletingId: string | null;
  deleteError: ApiError | null;
  onUpload: (file: File) => Promise<void>;
  onDocumentAdded: (document: DocumentItem, duplicate: boolean) => void;
  onDelete: (doc: DocumentItem) => Promise<void>;
  onBulkDeleteSuccess: (deletedIds: string[]) => void;
  onRetry: () => void;
  onDismissError: () => void;
  onDismissDeleteError: () => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  documents,
  loading,
  error,
  uploading,
  deletingId,
  deleteError,
  onUpload,
  onDocumentAdded,
  onDelete,
  onBulkDeleteSuccess,
  onRetry,
  onDismissError,
  onDismissDeleteError,
}) => {
  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-parchment-border pb-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-parchment-muted font-bold">Archive Corpus</p>
          <h2 id="documents-heading" className="font-serif text-2xl font-bold text-parchment-text">
            Document Management
          </h2>
        </div>
        <div className="text-xs text-parchment-muted">
          <span>Total records: </span>
          <strong className="text-parchment-text font-mono">{documents.length}</strong>
        </div>
      </div>

      {error && <ErrorBanner error={error} onDismiss={onDismissError} />}
      {deleteError && <ErrorBanner error={deleteError} onDismiss={onDismissDeleteError} />}

      <DocumentLibrary
        documents={documents}
        loading={loading}
        error={error}
        uploading={uploading}
        deletingId={deletingId}
        onUpload={onUpload}
        onDocumentAdded={onDocumentAdded}
        onDelete={onDelete}
        onBulkDeleteSuccess={onBulkDeleteSuccess}
        onRetry={onRetry}
      />
    </div>
  );
};
