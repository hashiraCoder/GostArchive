import React, { useState, useRef, useEffect } from "react";
import type { ConversationDetailResponse, ConversationMessage } from "../api/conversations";

interface ConversationThreadProps {
  conversation: ConversationDetailResponse | null;
  activeScope: string;
  scopeLabel: string;
  onSendMessage: (question: string) => Promise<void>;
  onRetryMessage: (clientTurnId: string, question: string) => Promise<void>;
  isOllamaOffline: boolean;
  isOllamaDaemonOffline: boolean;
  isModelMissing: boolean;
  sendingQuestion?: boolean;
}

export const ConversationThread: React.FC<ConversationThreadProps> = ({
  conversation,
  activeScope: _activeScope,
  scopeLabel,
  onSendMessage,
  onRetryMessage,
  isOllamaOffline,
  isOllamaDaemonOffline,
  isModelMissing,
  sendingQuestion = false,
}) => {
  const [inputQuestion, setInputQuestion] = useState("");
  const [retryingTurnId, setRetryingTurnId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages, sendingQuestion]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const clean = inputQuestion.trim();
    if (!clean || sendingQuestion || isOllamaOffline) return;
    setInputQuestion("");
    await onSendMessage(clean);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit(e);
    }
  };

  const handleRetry = async (asstMsg: ConversationMessage) => {
    if (!asstMsg.client_turn_id || !conversation) return;
    // Find matching user question for this turn
    const userMsg = conversation.messages.find(
      (m) => m.client_turn_id === asstMsg.client_turn_id && m.role === "user",
    );
    const questionText = userMsg ? userMsg.content : "";
    if (!questionText) return;

    try {
      setRetryingTurnId(asstMsg.client_turn_id);
      await onRetryMessage(asstMsg.client_turn_id, questionText);
    } finally {
      setRetryingTurnId(null);
    }
  };

  const messages = conversation?.messages || [];

  return (
    <div className="flex-1 flex flex-col border border-parchment-border rounded bg-parchment-surface overflow-hidden min-h-[500px]">
      {/* Thread Header */}
      <div className="px-5 py-3 border-b border-parchment-border bg-parchment-surface/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="font-serif font-bold text-base text-parchment-text leading-tight">
            {conversation ? conversation.title : "Active Discussion"}
          </h3>
          <p className="text-xs text-parchment-muted mt-0.5">
            {messages.length === 0
              ? "New discussion thread"
              : `${messages.length} message${messages.length === 1 ? "" : "s"} · Multi-turn context enabled`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-parchment-muted">
            Scope:{" "}
            <strong className="text-parchment-text font-medium bg-parchment-bg px-2 py-0.5 rounded border border-parchment-border">
              {scopeLabel}
            </strong>
          </span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5 max-h-[550px]">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[220px] text-center p-6 space-y-3">
            <div className="w-12 h-12 rounded-full bg-parchment-bg border border-parchment-border flex items-center justify-center font-serif text-xl text-parchment-accent">
              ?
            </div>
            <div className="max-w-md space-y-1">
              <h4 className="font-serif font-bold text-base text-parchment-text">
                Ask with Evidence
              </h4>
              <p className="text-xs text-parchment-muted leading-relaxed">
                Questions in GhostArchive are answered strictly using retrieved passages from{" "}
                <span className="font-medium text-parchment-text">{scopeLabel}</span>.
                Multi-turn questions will resolve pronouns and follow-ups while keeping facts grounded in original documents.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === "user";

            if (isUser) {
              return (
                <div key={msg.id || `user-${index}`} className="flex justify-end">
                  <div className="max-w-xl rounded-lg border border-parchment-border bg-parchment-bg/70 px-4 py-3 shadow-sm space-y-1">
                    <div className="flex items-center justify-between gap-3 text-[11px] text-parchment-muted">
                      <span className="font-semibold text-parchment-accent">You</span>
                      <div className="flex items-center gap-1.5">
                        {msg.scope_document_ids && msg.scope_document_ids.length > 0 && (
                          <span className="rounded bg-parchment-border/40 px-1.5 py-0.2 text-[10px]">
                            Scoped
                          </span>
                        )}
                        <span>
                          {msg.created_at
                            ? new Date(msg.created_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : ""}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-parchment-text leading-relaxed whitespace-pre-line">
                      {msg.content}
                    </p>
                  </div>
                </div>
              );
            }

            // Assistant Message
            const isPending = msg.status === "pending";
            const isFailed = msg.status === "failed";
            const isRetrying = retryingTurnId === msg.client_turn_id;

            return (
              <article
                key={msg.id || `asst-${index}`}
                className="max-w-3xl rounded border border-parchment-border bg-parchment-surface p-4 space-y-3.5 shadow-sm"
              >
                {/* Assistant Header */}
                <div className="flex items-center justify-between border-b border-parchment-border pb-2.5 text-xs text-parchment-muted">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded bg-parchment-accent text-parchment-surface flex items-center justify-center font-serif text-[11px] font-bold select-none">
                      G
                    </span>
                    <span className="font-semibold text-parchment-text">GhostArchive</span>
                    {msg.model && (
                      <span className="rounded bg-parchment-bg border border-parchment-border px-1.5 py-0.5 text-[10px]">
                        {msg.model}
                      </span>
                    )}
                  </div>
                  <div>
                    {isPending ? (
                      <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[11px] animate-pulse">
                        ● Generating…
                      </span>
                    ) : isFailed ? (
                      <span className="inline-flex items-center gap-1 text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded text-[11px] font-medium">
                        ✕ Turn Failed
                      </span>
                    ) : (
                      <span>
                        {msg.retrieval_count > 0
                          ? `Grounded in ${msg.retrieval_count} passage${msg.retrieval_count > 1 ? "s" : ""}`
                          : "Direct response"}
                      </span>
                    )}
                  </div>
                </div>

                {/* State: Pending */}
                {isPending && (
                  <div className="rounded border-l-4 border-amber-600 bg-amber-50/40 p-4 text-xs text-amber-900 space-y-1 animate-pulse">
                    <p className="font-semibold">Consulting evidence…</p>
                    <p className="text-[11px] text-amber-800">
                      Querying local vector store and generating a grounded answer with Gemma 3 1B.
                    </p>
                  </div>
                )}

                {/* State: Failed with Retry Option */}
                {isFailed && (
                  <div className="rounded border border-red-300 bg-red-50/70 p-4 text-xs text-red-900 space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold">Inference failed or timed out</p>
                        <p className="mt-0.5 text-[11px] text-red-800 leading-relaxed">
                          {msg.error_message || "The local Ollama service was unavailable."}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void handleRetry(msg)}
                        disabled={isRetrying || isOllamaOffline}
                        className="rounded bg-red-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-800 transition disabled:opacity-50 shrink-0"
                      >
                        {isRetrying ? "Retrying…" : "Retry Turn"}
                      </button>
                    </div>
                  </div>
                )}

                {/* State: Completed Answer */}
                {!isPending && !isFailed && (
                  <>
                    <h4 className="font-serif font-bold text-sm text-parchment-text">Answer</h4>
                    <div className="rounded border-l-4 border-parchment-accent bg-parchment-surface/60 p-3.5">
                      <p className="font-serif text-sm leading-relaxed text-parchment-text whitespace-pre-line">
                        {msg.direct_answer || msg.content}
                      </p>
                    </div>

                    {msg.archive_context && (
                      <div className="text-xs text-parchment-muted">
                        <strong>Archive context:</strong> {msg.archive_context}
                      </div>
                    )}

                    {msg.limitations && msg.limitations.length > 0 && (
                      <div className="rounded border border-amber-200/60 bg-amber-50/50 p-3 text-xs text-amber-900">
                        <strong>Scope &amp; Limitations:</strong>
                        <ul className="mt-1 list-disc pl-4 space-y-1 text-[11px]">
                          {msg.limitations.map((lim, idx) => (
                            <li key={idx}>{lim}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {msg.insufficient_evidence ? (
                      <div className="rounded bg-amber-50 border border-amber-200 p-2.5 text-xs text-amber-900">
                        Insufficient evidence in the retrieved archive passages.
                      </div>
                    ) : (
                      msg.citations &&
                      msg.citations.length > 0 && (
                        <div className="space-y-2 pt-1">
                          <div className="flex items-center justify-between text-[11px] text-parchment-muted uppercase tracking-wider font-semibold">
                            <h4 className="text-xs font-semibold uppercase tracking-widest text-parchment-muted">Sources</h4>
                            <span className="text-[10px] text-parchment-muted lowercase font-normal">
                              {msg.citations.length} passage{msg.citations.length > 1 ? "s" : ""}
                            </span>
                          </div>
                          <div className="space-y-2">
                            {msg.citations.map((citation) => (
                              <details
                                key={citation.chunk_id}
                                open
                                className="group rounded border border-parchment-border bg-parchment-surface/60 p-2.5 text-xs transition hover:border-parchment-accent"
                              >
                                <summary className="cursor-pointer font-medium flex items-center justify-between select-none">
                                  <span className="flex items-center gap-2">
                                    <span className="font-mono text-[10px] text-parchment-accent font-semibold">
                                      [{citation.chunk_id}]
                                    </span>
                                    <span>{citation.document_title || citation.filename}</span>
                                    {citation.page_number != null && (
                                      <span className="text-parchment-muted">
                                        (Page {citation.page_number})
                                      </span>
                                    )}
                                  </span>
                                  <span>
                                    {citation.document_exists === false ? (
                                      <span
                                        title="The original document was deleted, but this citation snapshot was permanently preserved"
                                        className="rounded border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-800 font-medium"
                                      >
                                        Historical Snapshot — Source removed
                                      </span>
                                    ) : (
                                      <span className="rounded border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[10px] text-emerald-800 font-medium">
                                        ✓ SQLite Verified
                                      </span>
                                    )}
                                  </span>
                                </summary>
                                <p className="mt-2 border-l-2 border-parchment-accent pl-2.5 text-xs leading-relaxed text-parchment-text">
                                  {citation.excerpt}
                                </p>
                              </details>
                            ))}
                          </div>
                        </div>
                      )
                    )}
                  </>
                )}
              </article>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Composer */}
      <div className="p-4 border-t border-parchment-border bg-parchment-surface/90 space-y-2">
        {/* Ollama Offline Guidance Alerts */}
        {isOllamaDaemonOffline && (
          <div
            role="alert"
            className="rounded border border-red-300 bg-red-50 p-2.5 text-xs text-red-900 space-y-0.5"
          >
            <p className="font-semibold">Ollama Local Model Offline</p>
            <p className="text-[11px] text-red-800">
              The local Ollama inference service is currently offline. Start Ollama with{" "}
              <code>ollama serve</code> to enable asking questions.
            </p>
          </div>
        )}

        {isModelMissing && (
          <div
            role="alert"
            className="rounded border border-amber-300 bg-amber-50 p-2.5 text-xs text-amber-900 space-y-0.5"
          >
            <p className="font-semibold">Ollama Model Missing</p>
            <p className="text-[11px] text-amber-800">
              Run <code>ollama pull gemma3:1b</code> to download the required local model.
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-2">
          <label htmlFor="archive-question" className="sr-only">
            Question
          </label>
          <div className="relative">
            <textarea
              id="archive-question"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sendingQuestion || isOllamaOffline}
              placeholder={
                isOllamaDaemonOffline
                  ? "Ollama service unavailable. Please start Ollama with 'ollama serve'…"
                  : isModelMissing
                  ? "Configured model missing. Please run 'ollama pull gemma3:1b'…"
                  : `Ask a question grounded in ${scopeLabel} (Press Enter to send)…`
              }
              rows={2}
              className="w-full rounded border border-parchment-border bg-parchment-surface px-3 py-2 text-xs leading-relaxed text-parchment-text placeholder:text-parchment-muted disabled:cursor-not-allowed disabled:bg-parchment-bg/60"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-parchment-muted">
              Evidence from: <strong className="text-parchment-text">{scopeLabel}</strong>
            </span>
            <button
              type="submit"
              disabled={sendingQuestion || !inputQuestion.trim() || isOllamaOffline}
              className="rounded bg-parchment-accent px-4 py-1.5 text-xs font-semibold text-parchment-surface hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sendingQuestion ? "Consulting evidence…" : "Ask archive"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
