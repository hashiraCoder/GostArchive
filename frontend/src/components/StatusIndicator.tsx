import React from "react";
import type { ApiError } from "../api/client";
import type { DependencyDetail, DependencyStatus, ReadyResponse } from "../api/health";
import { ErrorBanner } from "./ErrorBanner";

interface StatusIndicatorProps {
  readyData: ReadyResponse | null;
  loading: boolean;
  error: ApiError | null;
  onRetry?: () => void;
}

const statusConfig: Record<
  DependencyStatus,
  { label: string; icon: string; classes: string }
> = {
  ready: {
    label: "Ready",
    icon: "✓",
    classes: "bg-status-ready/10 text-status-ready border-status-ready/30",
  },
  degraded: {
    label: "Degraded",
    icon: "▲",
    classes: "bg-status-degraded/10 text-status-degraded border-status-degraded/30",
  },
  unavailable: {
    label: "Offline",
    icon: "✗",
    classes: "bg-status-unavailable/10 text-status-unavailable border-status-unavailable/30",
  },
};

const dependencyNames: Record<string, string> = {
  database: "SQLite DB",
  chroma: "Chroma Store",
  embedding_model: "Embeddings",
  ollama: "Ollama Model",
};

interface DependencyBadgeProps {
  name: string;
  detail: DependencyDetail;
}

const DependencyBadge: React.FC<DependencyBadgeProps> = ({ name, detail }) => {
  const cfg = statusConfig[detail.status] || statusConfig.unavailable;
  const displayName = dependencyNames[name] || name;

  return (
    <div
      role="status"
      aria-label={`${displayName}: ${cfg.label}${detail.message ? ` — ${detail.message}` : ""}`}
      title={detail.message ?? `${displayName} is ${cfg.label}`}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium border rounded ${cfg.classes}`}
    >
      <span aria-hidden="true" className="font-bold text-[10px]">
        {cfg.icon}
      </span>
      <span>{displayName}</span>
    </div>
  );
};

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  readyData,
  loading,
  error,
  onRetry,
}) => {
  if (error) {
    return (
      <div className="w-full">
        <ErrorBanner error={error} onRetry={onRetry} />
      </div>
    );
  }

  if (loading && !readyData) {
    return (
      <div
        role="status"
        aria-label="Checking system dependencies"
        className="flex items-center gap-2 text-xs text-parchment-muted animate-pulse"
      >
        <span className="inline-block w-2 h-2 rounded-full bg-parchment-border"></span>
        <span>Checking local archive services...</span>
      </div>
    );
  }

  if (!readyData) {
    return null;
  }

  const { dependencies } = readyData;

  return (
    <div
      role="status"
      aria-label="System status"
      className="flex flex-wrap items-center gap-2"
    >
      <DependencyBadge name="database" detail={dependencies.database} />
      <DependencyBadge name="chroma" detail={dependencies.chroma} />
      <DependencyBadge name="embedding_model" detail={dependencies.embedding_model} />
      <DependencyBadge name="ollama" detail={dependencies.ollama} />
    </div>
  );
};
