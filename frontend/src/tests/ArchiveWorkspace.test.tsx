import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ArchiveWorkspace } from "../components/ArchiveWorkspace";
import { listDocuments, deleteDocument, bulkDeleteDocuments } from "../api/documents";
import { searchDocuments } from "../api/search";
import { askQuestion } from "../api/chat";
import { getReady } from "../api/health";

vi.mock("../api/documents", () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  bulkDeleteDocuments: vi.fn(),
}));

vi.mock("../api/search", () => ({
  searchDocuments: vi.fn(),
}));

vi.mock("../api/chat", () => ({
  askQuestion: vi.fn(),
}));

vi.mock("../api/health", () => ({
  getReady: vi.fn(),
}));

const document1 = {
  id: "doc-1",
  filename: "field-report.txt",
  file_type: "txt",
  byte_size: 120,
  status: "ready",
  chunk_count: 1,
  created_at: "2026-10-29T00:00:00Z",
  updated_at: "2026-10-29T00:00:00Z",
};

const document2 = {
  id: "doc-2",
  filename: "botanical_notes.md",
  file_type: "md",
  byte_size: 240,
  status: "ready",
  chunk_count: 2,
  created_at: "2026-10-29T01:00:00Z",
  updated_at: "2026-10-29T01:00:00Z",
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(getReady).mockResolvedValue({
    status: "ok",
    app_version: "0.1.0",
    dependencies: {
      sqlite: { status: "ready" },
      chroma: { status: "ready" },
      embedding_model: { status: "ready" },
      ollama: { status: "ready" },
    },
  } as any);
  vi.mocked(listDocuments).mockResolvedValue({ items: [document1, document2], total: 2 });
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
  vi.mocked(bulkDeleteDocuments).mockResolvedValue({
    results: [
      { id: "doc-1", success: true },
      { id: "doc-2", success: true },
    ],
    total_deleted: 2,
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
    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    fireEvent.click(deleteButtons[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete document" }));

    await waitFor(() => expect(deleteDocument).toHaveBeenCalledWith("doc-1"));
    await waitFor(() => expect(screen.queryByText("field-report.txt")).not.toBeInTheDocument());
  });

  it("supports archive scope selection, passes document_ids, and invalidates search results on change", async () => {
    render(<ArchiveWorkspace />);

    expect(await screen.findByText("field-report.txt")).toBeInTheDocument();

    // Change scope to doc-1
    const scopeSelect = screen.getByLabelText("Active Scope:");
    fireEvent.change(scopeSelect, { target: { value: "doc-1" } });

    // Execute search under doc-1 scope
    fireEvent.change(screen.getByLabelText("Search query"), {
      target: { value: "remedy" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => {
      expect(searchDocuments).toHaveBeenCalledWith("remedy", ["doc-1"]);
    });
    expect(await screen.findByText("The recommended remedy is drainage.")).toBeInTheDocument();

    // Execute Ask under doc-1 scope
    fireEvent.change(screen.getByLabelText("Question"), {
      target: { value: "What remedy?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask archive" }));

    await waitFor(() => {
      expect(askQuestion).toHaveBeenCalledWith("What remedy?", ["doc-1"]);
    });

    // Invalidate results when changing scope
    fireEvent.change(scopeSelect, { target: { value: "all" } });
    expect(screen.queryByText("Answer")).not.toBeInTheDocument();
  });

  it("filters documents by filename, status, and file type", async () => {
    render(<ArchiveWorkspace />);

    expect(await screen.findByText("field-report.txt")).toBeInTheDocument();
    expect(screen.getByText("botanical_notes.md")).toBeInTheDocument();

    // Filter by filename
    fireEvent.change(screen.getByPlaceholderText("Filter by filename…"), {
      target: { value: "botanical" },
    });
    expect(screen.getByText("botanical_notes.md")).toBeInTheDocument();
    expect(screen.queryByText("field-report.txt")).not.toBeInTheDocument();

    // Reset filter
    fireEvent.change(screen.getByPlaceholderText("Filter by filename…"), {
      target: { value: "" },
    });
    expect(screen.getByText("field-report.txt")).toBeInTheDocument();

    // Filter by file type
    fireEvent.change(screen.getByLabelText("Filter by file type"), {
      target: { value: "txt" },
    });
    expect(screen.getByText("field-report.txt")).toBeInTheDocument();
    expect(screen.queryByText("botanical_notes.md")).not.toBeInTheDocument();
  });

  it("supports master selection and bulk deletion with confirmation", async () => {
    render(<ArchiveWorkspace />);

    expect(await screen.findByText("field-report.txt")).toBeInTheDocument();

    // Toggle master checkbox to select all on page
    const masterCheckbox = screen.getByLabelText("Select all documents on current page");
    fireEvent.click(masterCheckbox);

    // Expect bulk delete button
    const bulkDeleteBtn = screen.getByRole("button", { name: "Delete selected" });
    expect(bulkDeleteBtn).toBeInTheDocument();
    expect(screen.getByText("2 selected")).toBeInTheDocument();

    fireEvent.click(bulkDeleteBtn);

    // Confirmation dialog
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Delete 2 selected documents\?/i)).toBeInTheDocument();

    // Confirm deletion
    const confirmBtn = screen.getByRole("button", { name: "Delete 2 documents" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(bulkDeleteDocuments).toHaveBeenCalledWith(["doc-1", "doc-2"]);
    });

    await waitFor(() => {
      expect(screen.queryByText("field-report.txt")).not.toBeInTheDocument();
      expect(screen.queryByText("botanical_notes.md")).not.toBeInTheDocument();
    });
  });

  it("renders Ollama offline warning and disables Ask submission when Ollama is unavailable", async () => {
    vi.mocked(getReady).mockResolvedValue({
      status: "degraded",
      app_version: "0.1.0",
      dependencies: {
        sqlite: { status: "ready" },
        chroma: { status: "ready" },
        embedding_model: { status: "ready" },
        ollama: { status: "unavailable" },
      },
    } as any);

    render(<ArchiveWorkspace />);

    expect(await screen.findByText("Ollama Local Model Offline")).toBeInTheDocument();
    const textarea = screen.getByLabelText("Question");
    expect(textarea).toBeDisabled();
    const askButton = screen.getByRole("button", { name: "Ask archive" });
    expect(askButton).toBeDisabled();
  });
});
