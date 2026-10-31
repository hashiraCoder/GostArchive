import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConversationSidebar } from "../components/ConversationSidebar";
import type { ConversationSummary } from "../api/conversations";

const mockConversations: ConversationSummary[] = [
  {
    id: "conv-1",
    title: "Lantern Stack Discussion",
    created_at: "2026-10-30T10:00:00Z",
    updated_at: "2026-10-30T10:05:00Z",
    message_count: 4,
    last_message_preview: "We rejected Redis due to single-node constraint.",
  },
  {
    id: "conv-2",
    title: "Jaipur Trip Budget",
    created_at: "2026-10-29T14:00:00Z",
    updated_at: "2026-10-29T14:30:00Z",
    message_count: 2,
    last_message_preview: "Hotel budget was Rs 2,000 per night.",
  },
];

describe("ConversationSidebar", () => {
  it("renders conversation list and handles selection and creation", () => {
    const onSelect = vi.fn();
    const onCreate = vi.fn();
    const onRename = vi.fn();
    const onDelete = vi.fn();

    render(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId="conv-1"
        onSelectConversation={onSelect}
        onCreateConversation={onCreate}
        onRenameConversation={onRename}
        onDeleteConversation={onDelete}
      />
    );

    expect(screen.getByText("Lantern Stack Discussion")).toBeInTheDocument();
    expect(screen.getByText("Jaipur Trip Budget")).toBeInTheDocument();
    expect(screen.getByText("4 msgs")).toBeInTheDocument();

    // Select second conversation
    fireEvent.click(screen.getByText("Jaipur Trip Budget"));
    expect(onSelect).toHaveBeenCalledWith("conv-2");

    // Click new conversation
    fireEvent.click(screen.getByRole("button", { name: /New Conversation/i }));
    expect(onCreate).toHaveBeenCalled();
  });

  it("supports inline rename with validation", async () => {
    const onRename = vi.fn().mockResolvedValue(undefined);

    render(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId="conv-1"
        onSelectConversation={vi.fn()}
        onCreateConversation={vi.fn()}
        onRenameConversation={onRename}
        onDeleteConversation={vi.fn()}
      />
    );

    // Click rename button for first conversation
    const renameBtn = screen.getByLabelText("Rename Lantern Stack Discussion");
    fireEvent.click(renameBtn);

    const input = screen.getByDisplayValue("Lantern Stack Discussion");
    fireEvent.change(input, { target: { value: "Lantern V2 Architecture" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(onRename).toHaveBeenCalledWith("conv-1", "Lantern V2 Architecture");
    });
  });

  it("requires confirmation before deleting a conversation", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);

    render(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId="conv-1"
        onSelectConversation={vi.fn()}
        onCreateConversation={vi.fn()}
        onRenameConversation={vi.fn()}
        onDeleteConversation={onDelete}
      />
    );

    const deleteBtn = screen.getByLabelText("Delete Lantern Stack Discussion");
    fireEvent.click(deleteBtn);

    expect(screen.getByText("Delete conversation?")).toBeInTheDocument();
    expect(
      screen.getByText("All messages and citation snapshots will be permanently removed.")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Confirm Delete" }));

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith("conv-1");
    });
  });
});
