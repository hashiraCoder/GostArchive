import React, { useState } from "react";
import type { ConversationSummary } from "../../api/conversations";

interface HistoryViewProps {
  conversations: ConversationSummary[];
  loading: boolean;
  onSelectConversation: (id: string) => Promise<void>;
  onCreateConversation: () => Promise<void>;
  onRenameConversation: (id: string, newTitle: string) => Promise<void>;
  onDeleteConversation: (id: string) => Promise<void>;
  onNavigateToAsk: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  conversations,
  loading,
  onSelectConversation,
  onCreateConversation,
  onRenameConversation,
  onDeleteConversation,
  onNavigateToAsk,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleStartRename = (conv: ConversationSummary, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleSaveRename = async (id: string, e: React.FormEvent) => {
    e.preventDefault();
    if (!editTitle.trim()) return;
    await onRenameConversation(id, editTitle.trim());
    setEditingId(null);
  };

  const handleOpenConversation = async (id: string) => {
    await onSelectConversation(id);
    onNavigateToAsk();
  };

  const handleStartDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingId(id);
  };

  const handleConfirmDelete = async (id: string) => {
    await onDeleteConversation(id);
    setDeletingId(null);
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-parchment-border bg-parchment-surface p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-parchment-border pb-3">
          <div>
            <h3 className="font-serif font-bold text-xl text-parchment-text">Saved Discussions</h3>
            <p className="text-xs text-parchment-muted mt-0.5">
              Persistent multi-turn sessions with verified evidence snapshots
            </p>
          </div>
          <button
            type="button"
            onClick={async () => {
              await onCreateConversation();
              onNavigateToAsk();
            }}
            className="px-4 py-2 rounded-lg bg-parchment-accent text-parchment-surface text-xs font-semibold hover:bg-parchment-accent-hover transition shadow-sm"
          >
            + New Discussion
          </button>
        </div>

        {loading && conversations.length === 0 ? (
          <div className="py-8 text-center text-xs text-parchment-muted animate-pulse">
            Loading discussions…
          </div>
        ) : conversations.length === 0 ? (
          <div className="py-12 text-center text-xs text-parchment-muted space-y-2">
            <p>No saved conversations found.</p>
            <p>
              Ask questions in the{" "}
              <button
                type="button"
                onClick={onNavigateToAsk}
                className="text-parchment-accent underline font-semibold"
              >
                Ask Archive
              </button>{" "}
              workspace to build persistent memory threads.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-parchment-border/60 text-xs">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => handleOpenConversation(conv.id)}
                className="py-3.5 flex items-start justify-between gap-4 hover:bg-parchment-sidebar/40 px-3 rounded-lg transition cursor-pointer"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  {editingId === conv.id ? (
                    <form
                      onSubmit={(e) => handleSaveRename(conv.id, e)}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-2"
                    >
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        autoFocus
                        className="rounded border border-parchment-border bg-parchment-surface px-2.5 py-1 text-xs text-parchment-text font-semibold focus:outline-none focus:ring-1 focus:ring-parchment-accent"
                      />
                      <button
                        type="submit"
                        className="rounded bg-parchment-accent px-2.5 py-1 text-xs font-semibold text-parchment-surface"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="rounded border border-parchment-border px-2 py-1 text-xs text-parchment-muted"
                      >
                        Cancel
                      </button>
                    </form>
                  ) : (
                    <h4 className="font-bold text-parchment-text text-sm truncate">
                      {conv.title}
                    </h4>
                  )}

                  {conv.last_message_preview && (
                    <p className="text-parchment-muted text-xs line-clamp-1 italic">
                      "{conv.last_message_preview}"
                    </p>
                  )}

                  <div className="flex items-center gap-2 text-[11px] text-parchment-muted">
                    <span>Updated {formatDate(conv.updated_at)}</span>
                    <span>·</span>
                    <span className="font-medium text-parchment-text">
                      {conv.message_count} message{conv.message_count === 1 ? "" : "s"}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-center" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => handleOpenConversation(conv.id)}
                    className="px-3 py-1.5 rounded-lg border border-parchment-border bg-parchment-surface text-parchment-accent font-semibold hover:bg-parchment-sidebar transition text-xs"
                  >
                    Reopen
                  </button>
                  <button
                    type="button"
                    onClick={(e) => handleStartRename(conv, e)}
                    className="px-2.5 py-1.5 rounded-lg border border-parchment-border bg-parchment-surface text-parchment-muted hover:text-parchment-text transition text-xs"
                    title="Rename conversation"
                  >
                    Rename
                  </button>
                  <button
                    type="button"
                    onClick={(e) => handleStartDelete(conv.id, e)}
                    className="px-2.5 py-1.5 rounded-lg border border-status-unavailable/30 text-status-unavailable hover:bg-status-unavailable/10 transition text-xs font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirmation Modal for Deletion */}
      {deletingId && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-conv-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        >
          <div className="w-full max-w-sm rounded-xl border border-parchment-border bg-parchment-surface p-6 shadow-xl space-y-4">
            <h3 id="delete-conv-modal-title" className="font-serif text-lg font-bold text-parchment-text">
              Delete Discussion?
            </h3>
            <p className="text-xs text-parchment-muted leading-relaxed">
              This will permanently delete this conversation and its turn history. Source documents and indexed vectors remain unaffected.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeletingId(null)}
                className="px-3.5 py-2 rounded-lg border border-parchment-border text-xs font-semibold text-parchment-text hover:bg-parchment-sidebar"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleConfirmDelete(deletingId)}
                className="px-3.5 py-2 rounded-lg bg-status-unavailable text-white text-xs font-semibold hover:bg-red-800 shadow-sm"
              >
                Delete Conversation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
