import React, { useEffect, useState, useMemo, useCallback } from "react";
import { ApiException, type ApiError } from "../api/client";
import { askQuestion } from "../api/chat";
import { deleteDocument, listDocuments, uploadDocument, type DocumentItem } from "../api/documents";
import { searchDocuments, type SearchResult } from "../api/search";
import { summarizeArchive, type SummaryResponse } from "../api/summary";
import { getReady, type ReadyResponse } from "../api/health";
import {
  listConversations,
  getConversation,
  createConversation,
  updateConversation,
  deleteConversation,
  type ConversationSummary,
  type ConversationDetailResponse,
  type ConversationMessage,
} from "../api/conversations";
import { OverviewView } from "./views/OverviewView";
import { DocumentsView } from "./views/DocumentsView";
import { AskArchiveView } from "./views/AskArchiveView";
import { HistoryView } from "./views/HistoryView";
import { SystemStatusView } from "./views/SystemStatusView";
import { DocumentLibrary } from "./DocumentLibrary";
import { ErrorBanner } from "./ErrorBanner";
import { EmptyState } from "./EmptyState";
import { ConversationSidebar } from "./ConversationSidebar";
import { ConversationThread } from "./ConversationThread";

export type WorkspaceTab = "overview" | "documents" | "ask" | "conversations" | "status" | "all";

export interface ArchiveWorkspaceProps {
  initialTab?: WorkspaceTab;
}

const POLL_INTERVAL_MS = 30_000;

export const ArchiveWorkspace: React.FC<ArchiveWorkspaceProps> = ({ initialTab = "all" }) => {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>(initialTab);

  // Document state
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState<ApiError | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<ApiError | null>(null);

  // Scope selection state: "all" or specific document ID
  const [selectedScope, setSelectedScope] = useState<string>("all");

  // System readiness state
  const [readyStatus, setReadyStatus] = useState<ReadyResponse | null>(null);
  const [readyLoading, setReadyLoading] = useState(false);
  const [readyError, setReadyError] = useState<ApiError | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  // Search state
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<ApiError | null>(null);

  // Conversation persistence state
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationDetailResponse | null>(null);
  const [conversationsLoading, setConversationsLoading] = useState(false);
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

  const checkReadiness = useCallback(async () => {
    setReadyLoading(true);
    try {
      const data = await getReady();
      setReadyStatus(data);
      setReadyError(null);
      setLastChecked(new Date());
    } catch (err) {
      if (err instanceof ApiException) {
        setReadyError(err.error);
      } else {
        setReadyError({
          code: "UNKNOWN_ERROR",
          message: "Unable to retrieve readiness status.",
          retryable: true,
        });
      }
    } finally {
      setReadyLoading(false);
    }
  }, []);

  const loadConversations = async () => {
    try {
      setConversationsLoading(true);
      const res = await listConversations();
      setConversations(res.items);
    } catch {
      // In offline or mocked test environments, ignore
    } finally {
      setConversationsLoading(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
    void checkReadiness();
    void loadConversations();

    const interval = setInterval(() => {
      void checkReadiness();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkReadiness]);

  // Active status polling when documents are in non-terminal states
  const hasPendingDocuments = useMemo(() => {
    return documents.some((d) => {
      const s = d.status.toLowerCase();
      return s === "processing" || s === "queued" || s === "deleting";
    });
  }, [documents]);

  useEffect(() => {
    if (!hasPendingDocuments && !uploading) return;

    const pollInterval = setInterval(() => {
      void loadDocuments();
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [hasPendingDocuments, uploading]);

  const readyDocuments = useMemo(
    () => documents.filter((d) => d.status.toLowerCase() === "ready"),
    [documents]
  );

  const scopeLabel = useMemo(() => {
    if (selectedScope === "all") {
      return `Entire Archive (${readyDocuments.length} ready document${readyDocuments.length === 1 ? "" : "s"})`;
    }
    const doc = documents.find((d) => d.id === selectedScope);
    return doc ? doc.filename : "Selected Document";
  }, [selectedScope, documents, readyDocuments.length]);

  const ollamaService = readyStatus?.dependencies?.ollama_service || readyStatus?.dependencies?.ollama;
  const modelAvailable = readyStatus?.dependencies?.model_available || readyStatus?.dependencies?.ollama;

  const isOllamaDaemonOffline = ollamaService?.status === "unavailable";
  const isModelMissing =
    !isOllamaDaemonOffline &&
    (modelAvailable?.status === "unavailable" || modelAvailable?.status === "degraded");
  const isOllamaOffline = isOllamaDaemonOffline || isModelMissing;

  const handleScopeChange = (newScope: string) => {
    setSelectedScope(newScope);
    setSearchResults([]);
    setHasSearched(false);
    setActiveConversation(null);
    setActiveConversationId(null);
  };

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

  const handleDocumentAdded = (document: DocumentItem, duplicate: boolean) => {
    if (!duplicate) {
      setDocuments((current) => [document, ...current.filter((d) => d.id !== document.id)]);
    }
    void loadDocuments();
  };

  const handleBulkDeleteSuccess = (deletedIds: string[]) => {
    const idSet = new Set(deletedIds);
    setDocuments((current) => current.filter((item) => !idSet.has(item.id)));
    if (deletedIds.includes(selectedScope)) {
      setSelectedScope("all");
      setSearchResults([]);
      setHasSearched(false);
      setActiveConversation(null);
      setActiveConversationId(null);
    }
  };

  const handleDelete = async (doc: DocumentItem) => {
    setDeletingId(doc.id);
    setDeleteError(null);
    try {
      await deleteDocument(doc.id);
      setDocuments((current) => current.filter((item) => item.id !== doc.id));
      if (selectedScope === doc.id) {
        setSelectedScope("all");
        setSearchResults([]);
        setHasSearched(false);
        setActiveConversation(null);
        setActiveConversationId(null);
      }
    } catch (error) {
      const apiErr =
        error instanceof ApiException
          ? error.error
          : { code: "DELETE_FAILED", message: "Could not delete document.", retryable: true };
      setDeleteError(apiErr);
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
      const docIds = selectedScope === "all" ? undefined : [selectedScope];
      const res = docIds ? await searchDocuments(query.trim(), docIds) : await searchDocuments(query.trim());
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

  const handleSelectConversation = async (id: string) => {
    setActiveConversationId(id);
    try {
      const detail = await getConversation(id);
      setActiveConversation(detail);
      setChatError(null);
    } catch (err) {
      setChatError(
        err instanceof ApiException
          ? err.error
          : { code: "UNKNOWN_ERROR", message: "Failed to load conversation.", retryable: true }
      );
    }
  };

  const handleCreateConversation = async () => {
    try {
      const newConv = await createConversation("New Conversation");
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setActiveConversation({
        id: newConv.id,
        title: newConv.title,
        created_at: newConv.created_at,
        updated_at: newConv.updated_at,
        messages: [],
      });
      setChatError(null);
    } catch (err) {
      setChatError(
        err instanceof ApiException
          ? err.error
          : { code: "UNKNOWN_ERROR", message: "Failed to create conversation.", retryable: true }
      );
    }
  };

  const handleRenameConversation = async (id: string, newTitle: string) => {
    try {
      const updated = await updateConversation(id, newTitle);
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: updated.title } : c))
      );
      if (activeConversation?.id === id) {
        setActiveConversation((prev) => (prev ? { ...prev, title: updated.title } : null));
      }
    } catch (err) {
      setChatError(
        err instanceof ApiException
          ? err.error
          : { code: "UNKNOWN_ERROR", message: "Failed to rename conversation.", retryable: true }
      );
    }
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setActiveConversation(null);
      }
    } catch (err) {
      setChatError(
        err instanceof ApiException
          ? err.error
          : { code: "UNKNOWN_ERROR", message: "Failed to delete conversation.", retryable: true }
      );
    }
  };

  const generateTurnId = () => {
    return typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `turn-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  };

  const handleSendMessage = async (cleanQuestion: string) => {
    setAsking(true);
    setChatError(null);
    const clientTurnId = generateTurnId();
    const docIds = selectedScope === "all" ? undefined : [selectedScope];

    // Optimistically add user message and pending assistant message
    const optimisticUserMsg: ConversationMessage = {
      id: `opt-u-${Date.now()}`,
      conversation_id: activeConversationId || "temp",
      client_turn_id: clientTurnId,
      role: "user",
      content: cleanQuestion,
      status: "completed",
      limitations: [],
      insufficient_evidence: false,
      citations: [],
      retrieval_count: 0,
      scope_document_ids: docIds || [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const optimisticAsstMsg: ConversationMessage = {
      id: `opt-a-${Date.now()}`,
      conversation_id: activeConversationId || "temp",
      client_turn_id: clientTurnId,
      role: "assistant",
      content: "",
      status: "pending",
      limitations: [],
      insufficient_evidence: false,
      citations: [],
      retrieval_count: 0,
      scope_document_ids: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setActiveConversation((prev) => ({
      id: prev?.id || activeConversationId || "temp",
      title: prev?.title || cleanQuestion.slice(0, 30),
      created_at: prev?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [...(prev?.messages || []), optimisticUserMsg, optimisticAsstMsg],
    }));

    try {
      const response = activeConversationId
        ? await askQuestion(cleanQuestion, docIds, activeConversationId, clientTurnId)
        : (docIds ? await askQuestion(cleanQuestion, docIds) : await askQuestion(cleanQuestion));

      const convId = response.conversation_id || activeConversationId;
      if (convId && convId !== "temp") {
        setActiveConversationId(convId);
        try {
          const detail = await getConversation(convId);
          setActiveConversation(detail);
          void loadConversations();
          return;
        } catch {
          // Fall through to local synthesis (e.g. test environment)
        }
      }

      const completedAsstMsg: ConversationMessage = {
        id: response.message_id || `asst-${Date.now()}`,
        conversation_id: convId || "temp",
        client_turn_id: clientTurnId,
        role: "assistant",
        content: response.answer,
        status: "completed",
        direct_answer: response.direct_answer || response.answer,
        archive_context: response.archive_context,
        limitations: response.limitations || [],
        insufficient_evidence: response.insufficient_evidence,
        citations: (response.citations || []).map((c) => ({
          ...c,
          document_exists: c.document_exists !== false,
        })),
        retrieval_count: response.retrieval_count,
        model: response.model,
        scope_document_ids: docIds || [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setActiveConversation((prev) => ({
        id: prev?.id || "temp",
        title: prev?.title || cleanQuestion.slice(0, 30),
        created_at: prev?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: [
          ...(prev?.messages || []).filter((m) => m.client_turn_id !== clientTurnId),
          optimisticUserMsg,
          completedAsstMsg,
        ],
      }));
    } catch (error) {
      if (error instanceof ApiException) {
        setChatError(error.error);
      } else {
        setChatError({
          code: "UNKNOWN_ERROR",
          message: "Could not answer question.",
          retryable: true,
        });
      }

      setActiveConversation((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: prev.messages.map((m) =>
            m.client_turn_id === clientTurnId && m.role === "assistant"
              ? {
                  ...m,
                  status: "failed",
                  error_message:
                    error instanceof ApiException
                      ? error.error.message
                      : "Failed to generate answer.",
                }
              : m
          ),
        };
      });

      if (activeConversationId && activeConversationId !== "temp") {
        try {
          const detail = await getConversation(activeConversationId);
          setActiveConversation(detail);
        } catch {
          // Keep optimistic failed state
        }
      }
    } finally {
      setAsking(false);
    }
  };

  const handleRetryMessage = async (clientTurnId: string, retryQuestion: string) => {
    setAsking(true);
    setChatError(null);
    const docIds = selectedScope === "all" ? undefined : [selectedScope];

    setActiveConversation((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        messages: prev.messages.map((m) =>
          m.client_turn_id === clientTurnId && m.role === "assistant"
            ? { ...m, status: "pending", error_message: null }
            : m
        ),
      };
    });

    try {
      const response = await askQuestion(
        retryQuestion,
        docIds,
        activeConversationId || undefined,
        clientTurnId
      );

      const convId = response.conversation_id || activeConversationId;
      if (convId && convId !== "temp") {
        try {
          const detail = await getConversation(convId);
          setActiveConversation(detail);
          void loadConversations();
          return;
        } catch {
          // Fall through
        }
      }

      const completedAsstMsg: ConversationMessage = {
        id: response.message_id || `asst-${Date.now()}`,
        conversation_id: convId || "temp",
        client_turn_id: clientTurnId,
        role: "assistant",
        content: response.answer,
        status: "completed",
        direct_answer: response.direct_answer || response.answer,
        archive_context: response.archive_context,
        limitations: response.limitations || [],
        insufficient_evidence: response.insufficient_evidence,
        citations: (response.citations || []).map((c) => ({
          ...c,
          document_exists: c.document_exists !== false,
        })),
        retrieval_count: response.retrieval_count,
        model: response.model,
        scope_document_ids: docIds || [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setActiveConversation((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: prev.messages.map((m) =>
            m.client_turn_id === clientTurnId && m.role === "assistant" ? completedAsstMsg : m
          ),
        };
      });
    } catch (error) {
      if (error instanceof ApiException) {
        setChatError(error.error);
      } else {
        setChatError({
          code: "UNKNOWN_ERROR",
          message: "Retry failed.",
          retryable: true,
        });
      }
      setActiveConversation((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: prev.messages.map((m) =>
            m.client_turn_id === clientTurnId && m.role === "assistant"
              ? {
                  ...m,
                  status: "failed",
                  error_message:
                    error instanceof ApiException
                      ? error.error.message
                      : "Retry failed to generate answer.",
                }
              : m
          ),
        };
      });
    } finally {
      setAsking(false);
    }
  };

  const handleSummarize = async () => {
    setSummarizing(true);
    setSummaryError(null);
    try {
      const docId = selectedScope === "all" ? undefined : selectedScope;
      const res = await summarizeArchive(docId);
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

  const viewTitles: Record<WorkspaceTab, string> = {
    overview: "Archive Overview",
    documents: "Document Management",
    ask: "Ask Archive with Evidence",
    conversations: "Saved Conversations",
    status: "System Diagnostics & Health",
    all: "Complete Archive Workspace",
  };

  // If in tabbed mode (i.e. activeTab !== 'all')
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-parchment-bg text-parchment-text antialiased">
      {/* ── Persistent Desktop Sidebar ─────────────────────────────── */}
      <aside className="w-full md:w-64 bg-parchment-sidebar border-r border-parchment-border flex flex-col shrink-0">
        {/* Brand Header */}
        <div className="p-5 border-b border-parchment-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-parchment-accent text-parchment-surface flex items-center justify-center font-serif font-bold text-lg shadow-sm">
              G
            </div>
            <div>
              <h1 className="font-serif font-bold text-base tracking-tight text-parchment-text leading-tight">
                GhostArchive
              </h1>
              <p className="text-xs text-parchment-muted font-medium">Memory Retrieval</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav aria-label="Main Navigation" className="flex-1 p-3 space-y-1 overflow-y-auto">
          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === "overview"
                ? "bg-parchment-surface text-parchment-accent font-semibold shadow-sm border border-parchment-border"
                : "text-parchment-muted hover:bg-parchment-border/40"
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span>Overview</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("documents")}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === "documents"
                ? "bg-parchment-surface text-parchment-accent font-semibold shadow-sm border border-parchment-border"
                : "text-parchment-muted hover:bg-parchment-border/40"
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Documents</span>
            <span className="ml-auto text-xs font-semibold bg-parchment-border text-parchment-text px-2 py-0.5 rounded-full">
              {documents.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("ask")}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === "ask"
                ? "bg-parchment-surface text-parchment-accent font-semibold shadow-sm border border-parchment-border"
                : "text-parchment-muted hover:bg-parchment-border/40"
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>Ask Archive</span>
            <span className="ml-auto text-[10px] font-bold text-status-ready bg-status-ready/10 px-1.5 py-0.5 rounded">
              Core
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("conversations")}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === "conversations"
                ? "bg-parchment-surface text-parchment-accent font-semibold shadow-sm border border-parchment-border"
                : "text-parchment-muted hover:bg-parchment-border/40"
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Conversations</span>
            <span className="ml-auto text-xs font-semibold bg-parchment-border text-parchment-text px-2 py-0.5 rounded-full">
              {conversations.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("status")}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === "status"
                ? "bg-parchment-surface text-parchment-accent font-semibold shadow-sm border border-parchment-border"
                : "text-parchment-muted hover:bg-parchment-border/40"
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span>System Status</span>
            <span
              className={`ml-auto w-2 h-2 rounded-full ${
                isOllamaOffline ? "bg-status-unavailable" : "bg-status-ready"
              }`}
            />
          </button>
        </nav>

        {/* Compact System Badge at bottom of sidebar */}
        <div className="p-3 border-t border-parchment-border">
          <div className="rounded-lg bg-parchment-surface border border-parchment-border p-3 text-xs space-y-1.5 shadow-sm">
            <div className="flex items-center justify-between font-medium">
              <span className="text-parchment-text flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isOllamaOffline ? "bg-status-unavailable" : "bg-status-ready"
                  }`}
                />
                <span>{isOllamaOffline ? "Ollama Offline" : "Local AI Ready"}</span>
              </span>
              <span className="text-[10px] bg-parchment-border/60 text-parchment-muted px-1.5 py-0.5 rounded font-mono">
                100% Offline
              </span>
            </div>
            <p className="text-parchment-muted text-[11px] leading-tight">
              Gemma 3 1B · MiniLM-L6-v2
            </p>
          </div>
        </div>
      </aside>

      {/* ── Main Workspace Area ────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto bg-parchment-bg flex flex-col">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-10 bg-parchment-surface/90 backdrop-blur border-b border-parchment-border px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-serif font-bold text-lg text-parchment-text">
              {viewTitles[activeTab]}
            </span>
            <span className="text-xs text-parchment-muted">·</span>
            <span className="text-xs text-parchment-muted flex items-center gap-1.5">
              <span>Active Scope:</span>
              <span className="bg-parchment-sidebar text-parchment-accent font-medium px-2 py-0.5 rounded border border-parchment-border">
                {scopeLabel}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab("documents")}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-parchment-border bg-parchment-surface text-parchment-text hover:bg-parchment-sidebar transition"
            >
              + Import Files
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("ask")}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-parchment-accent text-parchment-surface hover:bg-parchment-accent-hover transition shadow-sm"
            >
              New Question
            </button>
          </div>
        </header>

        {/* Content View Container */}
        <div className="flex-1 p-6 max-w-6xl w-full mx-auto">
          {activeTab === "overview" && (
            <OverviewView
              documents={documents}
              conversations={conversations}
              readyStatus={readyStatus}
              onNavigate={setActiveTab}
              onSummarize={handleSummarize}
              summary={summary}
              summarizing={summarizing}
              summaryError={summaryError}
              onDismissSummaryError={() => setSummaryError(null)}
              isOllamaOffline={isOllamaOffline}
            />
          )}

          {activeTab === "documents" && (
            <DocumentsView
              documents={documents}
              loading={documentsLoading}
              error={documentsError}
              uploading={uploading}
              deletingId={deletingId}
              deleteError={deleteError}
              onUpload={handleUpload}
              onDocumentAdded={handleDocumentAdded}
              onDelete={handleDelete}
              onBulkDeleteSuccess={handleBulkDeleteSuccess}
              onRetry={() => void loadDocuments()}
              onDismissError={() => setDocumentsError(null)}
              onDismissDeleteError={() => setDeleteError(null)}
            />
          )}

          {activeTab === "ask" && (
            <AskArchiveView
              documents={documents}
              selectedScope={selectedScope}
              scopeLabel={scopeLabel}
              onScopeChange={handleScopeChange}
              query={query}
              setQuery={setQuery}
              searchResults={searchResults}
              hasSearched={hasSearched}
              searching={searching}
              searchError={searchError}
              onSearch={handleSearch}
              onDismissSearchError={() => setSearchError(null)}
              conversations={conversations}
              activeConversationId={activeConversationId}
              activeConversation={activeConversation}
              conversationsLoading={conversationsLoading}
              chatError={chatError}
              asking={asking}
              onSelectConversation={handleSelectConversation}
              onCreateConversation={handleCreateConversation}
              onRenameConversation={handleRenameConversation}
              onDeleteConversation={handleDeleteConversation}
              onSendMessage={handleSendMessage}
              onRetryMessage={handleRetryMessage}
              onDismissChatError={() => setChatError(null)}
              isOllamaOffline={isOllamaOffline}
              isOllamaDaemonOffline={isOllamaDaemonOffline}
              isModelMissing={isModelMissing}
            />
          )}

          {activeTab === "conversations" && (
            <HistoryView
              conversations={conversations}
              loading={conversationsLoading}
              onSelectConversation={handleSelectConversation}
              onCreateConversation={handleCreateConversation}
              onRenameConversation={handleRenameConversation}
              onDeleteConversation={handleDeleteConversation}
              onNavigateToAsk={() => setActiveTab("ask")}
            />
          )}

          {activeTab === "status" && (
            <SystemStatusView
              readyData={readyStatus}
              loading={readyLoading}
              error={readyError}
              onRefresh={checkReadiness}
              lastChecked={lastChecked}
            />
          )}

          {/* Unified 'all' view: keeps full compatibility for direct renders and comprehensive testing */}
          {activeTab === "all" && (
            <div className="space-y-10">
              {/* Scope Selection */}
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
                      onChange={(e) => handleScopeChange(e.target.value)}
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

              {/* Document Management */}
              <section aria-labelledby="documents-heading" className="space-y-4">
                <div>
                  <p className="text-xs uppercase tracking-widest text-parchment-muted font-bold">Archive Corpus</p>
                  <h2 id="documents-heading" className="font-serif text-2xl font-bold text-parchment-text">
                    Document Management
                  </h2>
                </div>

                {documentsError && <ErrorBanner error={documentsError} onDismiss={() => setDocumentsError(null)} />}
                {deleteError && <ErrorBanner error={deleteError} onDismiss={() => setDeleteError(null)} />}

                <DocumentLibrary
                  documents={documents}
                  loading={documentsLoading}
                  error={documentsError}
                  uploading={uploading}
                  deletingId={deletingId}
                  onUpload={handleUpload}
                  onDocumentAdded={handleDocumentAdded}
                  onDelete={handleDelete}
                  onBulkDeleteSuccess={handleBulkDeleteSuccess}
                  onRetry={() => void loadDocuments()}
                />
              </section>

              {/* Search Capability */}
              <section aria-labelledby="search-heading" className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-parchment-muted font-bold">Semantic &amp; Keyword</p>
                    <h2 id="search-heading" className="font-serif text-2xl font-bold text-parchment-text">
                      Search Documents
                    </h2>
                  </div>
                  <span className="text-xs text-parchment-muted">
                    Scope: <strong className="text-parchment-text">{scopeLabel}</strong>
                  </span>
                </div>

                <form onSubmit={handleSearch} className="flex gap-2">
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

                {searchError && <ErrorBanner error={searchError} onDismiss={() => setSearchError(null)} />}

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

              {/* Ask / Q&A Capability with Persistent Discussions */}
              <section aria-labelledby="ask-heading" className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
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

                {chatError && <ErrorBanner error={chatError} onDismiss={() => setChatError(null)} />}

                <div className="flex flex-col md:flex-row gap-5 items-stretch">
                  <ConversationSidebar
                    conversations={conversations}
                    activeConversationId={activeConversationId}
                    onSelectConversation={handleSelectConversation}
                    onCreateConversation={handleCreateConversation}
                    onRenameConversation={handleRenameConversation}
                    onDeleteConversation={handleDeleteConversation}
                    loading={conversationsLoading}
                  />
                  <ConversationThread
                    conversation={activeConversation}
                    activeScope={selectedScope}
                    scopeLabel={scopeLabel}
                    onSendMessage={handleSendMessage}
                    onRetryMessage={handleRetryMessage}
                    isOllamaOffline={isOllamaOffline}
                    isOllamaDaemonOffline={isOllamaDaemonOffline}
                    isModelMissing={isModelMissing}
                    sendingQuestion={asking}
                  />
                </div>
              </section>

              {/* Archive Summary Capability */}
              <section aria-labelledby="summary-heading" className="space-y-4 border-t border-parchment-border pt-8">
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-parchment-muted font-bold">Corpus Synthesis</p>
                    <h2 id="summary-heading" className="font-serif text-2xl font-bold text-parchment-text">
                      Archive Summary
                    </h2>
                  </div>
                  <button
                    type="button"
                    onClick={handleSummarize}
                    disabled={summarizing || isOllamaOffline}
                    className="rounded-lg bg-parchment-accent px-4 py-2 text-xs font-semibold text-parchment-surface hover:bg-parchment-accent-hover transition disabled:opacity-50"
                  >
                    {summarizing ? "Generating summary…" : "Generate Archive Summary"}
                  </button>
                </div>

                {summaryError && <ErrorBanner error={summaryError} onDismiss={() => setSummaryError(null)} />}

                {summary && (
                  <article className="rounded-xl border border-parchment-border bg-parchment-surface p-5 shadow-sm space-y-3">
                    <h3 className="font-serif text-base font-bold text-parchment-text">Synthesis</h3>
                    <p className="text-sm leading-relaxed text-parchment-text font-serif whitespace-pre-line">
                      {summary.summary}
                    </p>
                    {summary.limitations && summary.limitations.length > 0 && (
                      <div className="pt-2">
                        <span className="text-xs font-semibold text-parchment-muted">Scope &amp; Limitations:</span>
                        <ul className="mt-1 list-disc pl-4 space-y-1 text-xs text-parchment-muted">
                          {summary.limitations.map((lim, idx) => (
                            <li key={idx}>{lim}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </article>
                )}
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
