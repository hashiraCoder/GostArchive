import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ArchiveWorkspace } from "../components/ArchiveWorkspace";
import { listDocuments } from "../api/documents";
import { listConversations } from "../api/conversations";
import { getReady } from "../api/health";

vi.mock("../api/documents", () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  bulkDeleteDocuments: vi.fn(),
}));

vi.mock("../api/conversations", () => ({
  listConversations: vi.fn(),
  getConversation: vi.fn(),
  createConversation: vi.fn(),
  updateConversation: vi.fn(),
  deleteConversation: vi.fn(),
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

const mockDocs = [
  {
    id: "doc-1",
    filename: "field-report.txt",
    file_type: "txt",
    byte_size: 1024,
    status: "ready",
    chunk_count: 3,
    created_at: "2026-10-29T00:00:00Z",
    updated_at: "2026-10-29T00:00:00Z",
  },
  {
    id: "doc-2",
    filename: "spec.md",
    file_type: "md",
    byte_size: 2048,
    status: "ready",
    chunk_count: 5,
    created_at: "2026-10-29T01:00:00Z",
    updated_at: "2026-10-29T01:00:00Z",
  },
];

const mockConvs = [
  {
    id: "conv-1",
    title: "Project Architecture Discussion",
    created_at: "2026-10-30T10:00:00Z",
    updated_at: "2026-10-30T10:05:00Z",
    message_count: 4,
    last_message_preview: "Redis was rejected in favor of SQLite.",
  },
];

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(getReady).mockResolvedValue({
    overall: "ready",
    dependencies: {
      document_storage: { status: "ready", message: "SQLite tables & Chroma vector store active" },
      embedding_service: { status: "ready", message: "all-MiniLM-L6-v2 local sentence transformer" },
      ollama_service: { status: "ready", message: "HTTP loopback responsive" },
      model_available: { status: "ready", message: "Configured model verified" },
      model_inference: { status: "ready", message: "Inference response verified" },
      database: { status: "ready" },
      chroma: { status: "ready" },
      embedding_model: { status: "ready" },
      ollama: { status: "ready" },
    },
  });
  vi.mocked(listDocuments).mockResolvedValue({ items: mockDocs, total: 2 });
  vi.mocked(listConversations).mockResolvedValue({ items: mockConvs, total: 1 });
});

describe("Navigation and View Redesign", () => {
  it("renders Overview by default when initialTab='overview' with real metrics and recent docs", async () => {
    render(<ArchiveWorkspace initialTab="overview" />);

    expect(await screen.findByText("Welcome to your memory archive")).toBeInTheDocument();
    expect(screen.getByText("Personal Knowledge Repository")).toBeInTheDocument();

    // Verify Metric Cards reflect real data
    expect(screen.getByText("Total Documents")).toBeInTheDocument();
    expect(await screen.findByText("2 Ready in SQLite")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument(); // total chunks: 3 + 5 = 8
    expect(screen.getByText("Chroma HNSW + FTS5")).toBeInTheDocument();

    // Verify Recent Documents section
    expect(screen.getByText("Recent Archive Documents")).toBeInTheDocument();
    expect(screen.getByText("field-report.txt")).toBeInTheDocument();
    expect(screen.getByText("spec.md")).toBeInTheDocument();
  });

  it("switches to Documents view when clicking Documents in sidebar", async () => {
    render(<ArchiveWorkspace initialTab="overview" />);

    const nav = screen.getByRole("navigation", { name: "Main Navigation" });
    const docsTabBtn = within(nav).getByRole("button", { name: /Documents/i });
    fireEvent.click(docsTabBtn);

    expect(await screen.findByRole("heading", { name: "Document Management" })).toBeInTheDocument();
    expect(screen.getByText("Archive Corpus")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Filter by filename…")).toBeInTheDocument();
  });

  it("switches to Ask Archive view when clicking Ask Archive in sidebar", async () => {
    render(<ArchiveWorkspace initialTab="overview" />);

    const nav = screen.getByRole("navigation", { name: "Main Navigation" });
    const askTabBtn = within(nav).getByRole("button", { name: /Ask Archive/i });
    fireEvent.click(askTabBtn);

    expect(await screen.findByText("Question your archive")).toBeInTheDocument();
    expect(screen.getByText("Archive Scope Selection")).toBeInTheDocument();
    expect(screen.getByLabelText("Question")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask archive" })).toBeInTheDocument();
  });

  it("switches to Conversations view when clicking Conversations in sidebar", async () => {
    render(<ArchiveWorkspace initialTab="overview" />);

    const nav = screen.getByRole("navigation", { name: "Main Navigation" });
    const convTabBtn = within(nav).getByRole("button", { name: /Conversations/i });
    fireEvent.click(convTabBtn);

    expect(await screen.findByText("Saved Discussions")).toBeInTheDocument();
    expect(screen.getByText("Project Architecture Discussion")).toBeInTheDocument();
    expect(screen.getByText(/"Redis was rejected in favor of SQLite."/)).toBeInTheDocument();
  });

  it("switches to System Status view when clicking System Status in sidebar", async () => {
    render(<ArchiveWorkspace initialTab="overview" />);

    const nav = screen.getByRole("navigation", { name: "Main Navigation" });
    const statusTabBtn = within(nav).getByRole("button", { name: /System Status/i });
    fireEvent.click(statusTabBtn);

    expect(await screen.findByText("System Subsystem Diagnostics")).toBeInTheDocument();
    expect(screen.getByText("1. Document Storage (SQLite + Chroma)")).toBeInTheDocument();
    expect(screen.getByText("2. Embedding Service")).toBeInTheDocument();
    expect(screen.getByText("3. Ollama Daemon Connectivity")).toBeInTheDocument();
    expect(screen.getByText("4. Model Availability")).toBeInTheDocument();
    expect(screen.getByText("5. Model Inference Verification")).toBeInTheDocument();
    expect(screen.getByText("Local-First Security Guarantees")).toBeInTheDocument();
  });

  it("navigates directly using header action buttons", async () => {
    render(<ArchiveWorkspace initialTab="overview" />);

    // Click "+ Import Files" in top header
    const importBtn = screen.getByRole("button", { name: "+ Import Files" });
    fireEvent.click(importBtn);
    expect(await screen.findByRole("heading", { name: "Document Management" })).toBeInTheDocument();

    // Click "New Question" in top header
    const newQuestionBtn = screen.getByRole("button", { name: "New Question" });
    fireEvent.click(newQuestionBtn);
    expect(await screen.findByText("Question your archive")).toBeInTheDocument();
  });
});
