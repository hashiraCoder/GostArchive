import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ArchiveWorkspace } from "../components/ArchiveWorkspace";
import { listDocuments, deleteDocument } from "../api/documents";
import { searchDocuments } from "../api/search";
import { askQuestion } from "../api/chat";

vi.mock("../api/documents", () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
}));

vi.mock("../api/search", () => ({
  searchDocuments: vi.fn(),
}));

vi.mock("../api/chat", () => ({
  askQuestion: vi.fn(),
}));

const document = {
  id: "doc-1",
  filename: "field-report.txt",
  file_type: "txt",
  byte_size: 120,
  status: "ready",
  chunk_count: 1,
  created_at: "2026-10-29T00:00:00Z",
  updated_at: "2026-10-29T00:00:00Z",
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(listDocuments).mockResolvedValue({ items: [document], total: 1 });
  vi.mocked(searchDocuments).mockResolvedValue({
    items: [{
      chunk_id: "chunk-1",
      document_id: "doc-1",
      filename: "field-report.txt",
      page_number: null,
      text: "The recommended remedy is drainage.",
      start_char: 0,
      end_char: 36,
      score: 0.9,
    }],
    total: 1,
  });
  vi.mocked(askQuestion).mockResolvedValue({
    answer: "The recommended remedy is drainage.",
    insufficient_evidence: false,
    citations: [{
      chunk_id: "chunk-1",
      document_id: "doc-1",
      filename: "field-report.txt",
      page_number: null,
      excerpt: "The recommended remedy is drainage.",
    }],
    retrieval_count: 1,
    model: "gemma3:1b",
  });
});

describe("ArchiveWorkspace", () => {
  it("supports search, grounded questions, and citation inspection", async () => {
    render(<ArchiveWorkspace />);

    expect(await screen.findByText("field-report.txt")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search query"), {
      target: { value: "What remedy was recommended?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByText("The recommended remedy is drainage.")).toBeInTheDocument();
    expect(searchDocuments).toHaveBeenCalledWith("What remedy was recommended?");

    fireEvent.change(screen.getByLabelText("Question"), {
      target: { value: "What remedy was recommended?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask archive" }));
    expect(await screen.findByText("Answer")).toBeInTheDocument();
    expect(screen.getByText("Sources")).toBeInTheDocument();
    expect(screen.getAllByText("The recommended remedy is drainage.")).toHaveLength(3);
  });

  it("confirms document deletion and removes it after success", async () => {
    vi.mocked(deleteDocument).mockResolvedValue();
    render(<ArchiveWorkspace />);

    expect(await screen.findByText("field-report.txt")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete document" }));

    await waitFor(() => expect(deleteDocument).toHaveBeenCalledWith("doc-1"));
    await waitFor(() => expect(screen.queryByText("field-report.txt")).not.toBeInTheDocument());
  });
});
