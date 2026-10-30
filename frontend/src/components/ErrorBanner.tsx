import React from "react";
import type { ApiError } from "../api/client";

interface ErrorBannerProps {
  error: ApiError;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  error,
  onRetry,
  onDismiss,
}) => {
  return (
    <div
      role="alert"
      className="p-3 bg-red-50 border border-status-unavailable/30 text-status-unavailable rounded-md flex items-start justify-between gap-3 text-sm"
    >
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-xs tracking-wider uppercase bg-status-unavailable/10 px-1.5 py-0.5 rounded">
            {error.code}
          </span>
          {error.retryable && (
            <span className="text-xs text-parchment-muted italic">
              (Retryable)
            </span>
          )}
        </div>
        <p className="text-parchment-text leading-snug">{error.message}</p>
      </div>

      <div className="flex items-center gap-2 self-center">
        {error.retryable && onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-2.5 py-1 text-xs font-medium bg-parchment-surface border border-parchment-border text-parchment-text rounded hover:bg-parchment-bg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-parchment-accent"
          >
            Try again
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label="Dismiss error banner"
            className="p-1 text-parchment-muted hover:text-parchment-text rounded"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};
