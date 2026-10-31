import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConversationThread } from "../components/ConversationThread";
import type { ConversationDetailResponse } from "../api/conversations";

const mockThread: ConversationDetailResponse = {
  id: "conv-101",
  title: "Ancient Architecture Discussion",
  created_at: "2026-10-30T10:00:00Z",
  updated_at: "2026-10-30T10:05:00Z",
  messages: [
    {
      id: "msg-1",
      conversation_id: "conv-101",
      client_turn_id: "turn-1",
      role: "user",
      content: "When was the stone aqueduct completed?",
      status: "completed",
      limitations: [],
      insufficient_evidence: false,
      citations: [],
      retrieval_count: 0,
      scope_document_ids: ["doc-aqueduct"],
      created_at: "2026-10-30T10:00:00Z",
      updated_at: "2026-10-30T10:00:00Z",
    },
    {
      id: "msg-2",
      conversation_id: "conv-101",
      client_turn_id: "turn-1",
      role: "assistant",
      content: "The stone aqueduct was completed in 1420.",
      status: "completed",
      direct_answer: "The stone aqueduct was completed in 1420.",
      archive_context: "Constructed under Chief Mason Valerius.",
      limitations: ["Construction records for the eastern arcades are damaged."],
      insufficient_evidence: false,
      citations: [
        {
          chunk_id: "c-100",
          document_id: "doc-aqueduct",
          filename: "aqueduct_survey.txt",
          document_title: "Aqueduct Survey",
          page_number: 14,
          excerpt: "Aqueduct masonry was finalized in 1420.",
          evidence_type: "direct",
          document_exists: true,
        },
        {
          chunk_id: "c-200",
          document_id: "doc-lost",
          filename: "lost_records.txt",
          document_title: "Lost Records",
          page_number: null,
          excerpt: "Eastern arcade reports.",
          evidence_type: "direct",
          document_exists: false, // Deleted source document
        },
      ],
      retrieval_count: 2,
      model: "gemma3:1b",
      scope_document_ids: ["doc-aqueduct"],
      created_at: "2026-10-30T10:00:05Z",
      updated_at: "2026-10-30T10:00:05Z",
    },
    {
      id: "msg-3",
      conversation_id: "conv-101",
      client_turn_id: "turn-2",
      role: "user",
      content: "Who funded the restoration?",
      status: "completed",
      limitations: [],
      insufficient_evidence: false,
      citations: [],
      retrieval_count: 0,
      scope_document_ids: [],
      created_at: "2026-10-30T10:02:00Z",
      updated_at: "2026-10-30T10:02:00Z",
    },
    {
      id: "msg-4",
      conversation_id: "conv-101",
      client_turn_id: "turn-2",
      role: "assistant",
      content: "",
      status: "failed",
      error_message: "The local Ollama inference service is unavailable.",
      limitations: [],
      insufficient_evidence: false,
      citations: [],
      retrieval_count: 0,
      scope_document_ids: [],
      created_at: "2026-10-30T10:02:05Z",
      updated_at: "2026-10-30T10:02:05Z",
    },
  ],
};

describe("ConversationThread", () => {
  it("renders chronological turns with citations and status decorations", () => {
    render(
      <ConversationThread
        conversation={mockThread}
        activeScope="all"
        scopeLabel="Entire Archive"
        onSendMessage={vi.fn()}
        onRetryMessage={vi.fn()}
        isOllamaOffline={false}
        isOllamaDaemonOffline={false}
        isModelMissing={false}
      />
    );

    // Turn 1
    expect(screen.getByText("When was the stone aqueduct completed?")).toBeInTheDocument();
    expect(screen.getByText("The stone aqueduct was completed in 1420.")).toBeInTheDocument();
    expect(screen.getByText("Constructed under Chief Mason Valerius.")).toBeInTheDocument();

    // Citation existence badges
    expect(screen.getByText("✓ SQLite Verified")).toBeInTheDocument();
    expect(screen.getByText("Historical Snapshot — Source removed")).toBeInTheDocument();

    // Turn 2: Failed state with Retry button
    expect(screen.getByText("Who funded the restoration?")).toBeInTheDocument();
    expect(screen.getByText("The local Ollama inference service is unavailable.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry Turn" })).toBeInTheDocument();
  });

  it("handles retry of a failed turn using its client_turn_id", async () => {
    const onRetry = vi.fn().mockResolvedValue(undefined);

    render(
      <ConversationThread
        conversation={mockThread}
        activeScope="all"
        scopeLabel="Entire Archive"
        onSendMessage={vi.fn()}
        onRetryMessage={onRetry}
        isOllamaOffline={false}
        isOllamaDaemonOffline={false}
        isModelMissing={false}
      />
    );

    const retryBtn = screen.getByRole("button", { name: "Retry Turn" });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(onRetry).toHaveBeenCalledWith("turn-2", "Who funded the restoration?");
    });
  });

  it("submits a new question through onSendMessage", async () => {
    const onSend = vi.fn().mockResolvedValue(undefined);

    render(
      <ConversationThread
        conversation={mockThread}
        activeScope="all"
        scopeLabel="Entire Archive"
        onSendMessage={onSend}
        onRetryMessage={vi.fn()}
        isOllamaOffline={false}
        isOllamaDaemonOffline={false}
        isModelMissing={false}
      />
    );

    const textarea = screen.getByLabelText("Question");
    fireEvent.change(textarea, { target: { value: "Where were the quarries located?" } });

    const submitBtn = screen.getByRole("button", { name: "Ask archive" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith("Where were the quarries located?");
    });
  });
});
