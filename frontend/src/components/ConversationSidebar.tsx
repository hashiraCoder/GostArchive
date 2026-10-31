import React, { useState } from "react";
import type { ConversationSummary } from "../api/conversations";

interface ConversationSidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onCreateConversation: () => void;
  onRenameConversation: (id: string, newTitle: string) => Promise<void>;
  onDeleteConversation: (id: string) => Promise<void>;
  loading?: boolean;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
  onRenameConversation,
  onDeleteConversation,
  loading = false,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase().trim()),
  );

  const handleStartRename = (conv: ConversationSummary, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditingTitle(conv.title);
  };

  const handleSaveRename = async (id: string, e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = editingTitle.trim();
    if (!clean) return;
    try {
      setActionInProgress(true);
      await onRenameConversation(id, clean);
      setEditingId(null);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleCancelRename = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setEditingId(null);
    setEditingTitle("");
  };

  const handleDeleteClick = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmDeleteId(id);
  };

  const handleConfirmDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setActionInProgress(true);
      await onDeleteConversation(id);
      setConfirmDeleteId(null);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmDeleteId(null);
  };

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <aside
      aria-label="Conversation History"
      className="w-full md:w-80 flex flex-col border border-parchment-border rounded bg-parchment-surface/70 backdrop-blur-sm overflow-hidden"
    >
      {/* Header & New Conversation */}
      <div className="p-3 border-b border-parchment-border space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-serif font-bold text-sm tracking-wide text-parchment-text">
            Conversations
          </h3>
          <span className="text-xs text-parchment-muted">
            {conversations.length} total
          </span>
        </div>
        <button
          type="button"
          onClick={onCreateConversation}
          disabled={loading || actionInProgress}
          className="w-full flex items-center justify-center gap-1.5 rounded bg-parchment-accent px-3 py-1.5 text-xs font-semibold text-parchment-surface hover:opacity-90 transition disabled:opacity-50"
        >
          <span className="text-sm font-bold">+</span>
          <span>New Conversation</span>
        </button>
        {conversations.length > 3 && (
          <div>
            <label htmlFor="conversation-filter" className="sr-only">
              Filter conversations
            </label>
            <input
              id="conversation-filter"
              type="text"
              placeholder="Search conversations…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded border border-parchment-border bg-parchment-surface px-2.5 py-1 text-xs text-parchment-text placeholder:text-parchment-muted"
            />
          </div>
        )}
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto max-h-[460px] divide-y divide-parchment-border/50">
        {loading && conversations.length === 0 ? (
          <div className="p-4 text-center text-xs text-parchment-muted">
            Loading conversations…
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="p-6 text-center text-xs text-parchment-muted space-y-1">
            <p className="font-medium text-parchment-text">
              {searchQuery ? "No matching conversations" : "No saved conversations"}
            </p>
            <p className="text-[11px]">
              {searchQuery
                ? "Try a different search term"
                : "Ask a question below or start a new thread to persist your discussion."}
            </p>
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isActive = conv.id === activeConversationId;
            const isEditing = editingId === conv.id;
            const isDeleting = confirmDeleteId === conv.id;

            return (
              <div
                key={conv.id}
                role="button"
                tabIndex={0}
                onClick={() => onSelectConversation(conv.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    onSelectConversation(conv.id);
                  }
                }}
                className={`group relative p-3 text-left transition cursor-pointer select-none ${
                  isActive
                    ? "bg-parchment-surface border-l-4 border-parchment-accent"
                    : "hover:bg-parchment-surface/50"
                }`}
              >
                {isEditing ? (
                  <form
                    onSubmit={(e) => void handleSaveRename(conv.id, e)}
                    onClick={(e) => e.stopPropagation()}
                    className="space-y-2"
                  >
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      autoFocus
                      maxLength={200}
                      className="w-full rounded border border-parchment-accent bg-parchment-surface px-2 py-1 text-xs font-medium text-parchment-text"
                    />
                    <div className="flex justify-end gap-1.5 text-xs">
                      <button
                        type="button"
                        onClick={handleCancelRename}
                        className="px-2 py-0.5 rounded border border-parchment-border text-parchment-muted hover:bg-parchment-bg"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={actionInProgress || !editingTitle.trim()}
                        className="px-2 py-0.5 rounded bg-parchment-accent text-parchment-surface font-medium disabled:opacity-50"
                      >
                        Save
                      </button>
                    </div>
                  </form>
                ) : isDeleting ? (
                  <div
                    onClick={(e) => e.stopPropagation()}
                    className="space-y-2 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-900"
                  >
                    <p className="font-semibold">Delete conversation?</p>
                    <p className="text-[11px] text-red-700">
                      All messages and citation snapshots will be permanently removed.
                    </p>
                    <div className="flex justify-end gap-1.5 pt-1">
                      <button
                        type="button"
                        onClick={handleCancelDelete}
                        className="px-2 py-0.5 rounded border border-red-200 bg-white text-xs text-red-800 hover:bg-red-50"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={(e) => void handleConfirmDelete(conv.id, e)}
                        disabled={actionInProgress}
                        className="px-2 py-0.5 rounded bg-red-700 text-xs text-white font-medium hover:bg-red-800 disabled:opacity-50"
                      >
                        Confirm Delete
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-start justify-between gap-1">
                      <h4
                        className={`text-xs font-semibold truncate ${
                          isActive ? "text-parchment-text" : "text-parchment-text/90"
                        }`}
                        title={conv.title}
                      >
                        {conv.title}
                      </h4>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={(e) => handleStartRename(conv, e)}
                          title="Rename conversation"
                          aria-label={`Rename ${conv.title}`}
                          className="p-1 rounded text-parchment-muted hover:text-parchment-text hover:bg-parchment-border/40"
                        >
                          ✎
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteClick(conv.id, e)}
                          title="Delete conversation"
                          aria-label={`Delete ${conv.title}`}
                          className="p-1 rounded text-red-700 hover:text-red-900 hover:bg-red-100"
                        >
                          🗑
                        </button>
                      </div>
                    </div>

                    {conv.last_message_preview && (
                      <p className="mt-1 text-[11px] text-parchment-muted line-clamp-2 leading-relaxed">
                        {conv.last_message_preview}
                      </p>
                    )}

                    <div className="mt-2 flex items-center justify-between text-[10px] text-parchment-muted">
                      <span>{formatDate(conv.updated_at)}</span>
                      <span className="rounded bg-parchment-border/40 px-1.5 py-0.5 font-medium">
                        {conv.message_count} {conv.message_count === 1 ? "msg" : "msgs"}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
