import React, { useEffect, useState, useCallback } from "react";
import { getReady, type ReadyResponse } from "../api/health";
import { ApiException, type ApiError } from "../api/client";
import { StatusIndicator } from "./StatusIndicator";

interface AppShellProps {
  children: React.ReactNode;
}

const POLL_INTERVAL_MS = 30_000; // 30-second automatic polling

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [readyData, setReadyData] = useState<ReadyResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getReady();
      setReadyData(data);
      setError(null);
      setLastChecked(new Date());
    } catch (err) {
      if (err instanceof ApiException) {
        setError(err.error);
      } else {
        setError({
          code: "UNKNOWN_ERROR",
          message: "Unable to retrieve readiness status.",
          retryable: true,
        });
      }
      setReadyData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return (
    <div className="min-h-screen flex flex-col bg-parchment-bg text-parchment-text">
      {/* Top Header */}
      <header className="border-b border-parchment-border bg-parchment-surface/80 backdrop-blur-sm sticky top-0 z-10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span
              className="w-8 h-8 rounded bg-parchment-accent text-parchment-surface flex items-center justify-center font-serif font-bold text-lg select-none"
              aria-hidden="true"
            >
              G
            </span>
            <div>
              <h1 className="font-serif text-xl font-bold tracking-tight text-parchment-text leading-none">
                GhostArchive
              </h1>
              <p className="text-xs text-parchment-muted tracking-wide mt-0.5">
                Local-first evidence-grounded memory explorer
              </p>
            </div>
          </div>

          <nav aria-label="Main Navigation" className="flex items-center gap-1">
            <span className="px-3 py-1.5 text-xs font-medium text-parchment-accent bg-parchment-bg rounded border border-parchment-border">
              Archive
            </span>
            <span className="px-3 py-1.5 text-xs text-parchment-muted cursor-not-allowed">
              Search
            </span>
            <span className="px-3 py-1.5 text-xs text-parchment-muted cursor-not-allowed">
              Ask
            </span>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        {children}
      </main>

      {/* Persistent Bottom Status Strip with Automatic 30s Polling */}
      <footer
        className="border-t border-parchment-border bg-parchment-surface px-6 py-3 text-xs"
        role="region"
        aria-label="Archive system status"
      >
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-parchment-muted uppercase text-[10px] tracking-wider">
              System Services
            </span>
            <StatusIndicator
              readyData={readyData}
              loading={loading}
              error={error}
              onRetry={fetchStatus}
            />
          </div>

          <div className="flex items-center gap-2 text-parchment-muted text-[11px] self-end sm:self-center">
            {lastChecked && (
              <span>
                Polled {lastChecked.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </span>
            )}
            <span className="text-parchment-border">•</span>
            <span>Local loopback (127.0.0.1)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
