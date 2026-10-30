import React from "react";

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No documents in archive",
  message = "Import .txt or .md files to begin exploring your records.",
  actionText,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border-2 border-dashed border-parchment-border rounded-lg bg-parchment-surface/50 max-w-lg mx-auto my-12">
      <div
        className="w-12 h-12 mb-3 text-parchment-accent/70 flex items-center justify-center"
        aria-hidden="true"
      >
        <svg
          className="w-10 h-10"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>
      <h3 className="font-serif text-lg font-semibold text-parchment-text mb-1">
        {title}
      </h3>
      <p className="text-sm text-parchment-muted max-w-sm mb-4 leading-relaxed">
        {message}
      </p>
      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="px-4 py-2 text-sm font-medium bg-parchment-accent text-parchment-surface rounded hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-parchment-accent"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
