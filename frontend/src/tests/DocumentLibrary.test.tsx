import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DocumentLibrary } from "../components/DocumentLibrary";
import { uploadDocument } from "../api/documents";

vi.mock("../api/documents", () => ({
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  bulkDeleteDocuments: vi.fn(),
}));

describe("DocumentLibrary Component", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("processes uploaded files through queue with a single uploadDocument call per file", async () => {
    const mockDoc = {
      id: "doc-uploaded-1",
      filename: "test_notes.txt",
      file_type: "txt",
      byte_size: 150,
      status: "ready",
      chunk_count: 1,
      created_at: "2026-10-31T00:00:00Z",
      updated_at: "2026-10-31T00:00:00Z",
    };

    vi.mocked(uploadDocument).mockResolvedValue({
      document: mockDoc,
      duplicate: false,
    });

    const onDocumentAdded = vi.fn();
    const onDelete = vi.fn();
    const onRetry = vi.fn();

    const { container } = render(
      <DocumentLibrary
        documents={[]}
        loading={false}
        error={null}
        deletingId={null}
        onDocumentAdded={onDocumentAdded}
        onDelete={onDelete}
        onRetry={onRetry}
      />
    );

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeNull();

    const file = new File(["test note content"], "test_notes.txt", { type: "text/plain" });
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploadDocument).toHaveBeenCalledTimes(1);
      expect(uploadDocument).toHaveBeenCalledWith(file);
    });

    await waitFor(() => {
      expect(onDocumentAdded).toHaveBeenCalledWith(mockDoc, false);
      expect(screen.getByText("✓ Imported")).toBeInTheDocument();
    });
  });

  it("displays failure message and allows retry when upload fails", async () => {
    vi.mocked(uploadDocument).mockRejectedValueOnce(new Error("Network timeout"));

    const onDocumentAdded = vi.fn();
    const onDelete = vi.fn();
    const onRetry = vi.fn();

    const { container } = render(
      <DocumentLibrary
        documents={[]}
        loading={false}
        error={null}
        deletingId={null}
        onDocumentAdded={onDocumentAdded}
        onDelete={onDelete}
        onRetry={onRetry}
      />
    );

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["bad content"], "failed.txt", { type: "text/plain" });
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploadDocument).toHaveBeenCalledTimes(1);
      expect(screen.getByText("✕ Network timeout")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    });

    // Mock success on retry
    const mockDoc = {
      id: "doc-retry",
      filename: "failed.txt",
      file_type: "txt",
      byte_size: 100,
      status: "ready",
      chunk_count: 1,
      created_at: "2026-10-31T00:00:00Z",
      updated_at: "2026-10-31T00:00:00Z",
    };
    vi.mocked(uploadDocument).mockResolvedValueOnce({
      document: mockDoc,
      duplicate: false,
    });

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(uploadDocument).toHaveBeenCalledTimes(2);
      expect(screen.getByText("✓ Imported")).toBeInTheDocument();
    });
  });

  it("renders status badges with error details", () => {
    const documents = [
      {
        id: "doc-err",
        filename: "error_doc.txt",
        file_type: "txt",
        byte_size: 200,
        status: "error",
        chunk_count: 0,
        created_at: "2026-10-31T00:00:00Z",
        updated_at: "2026-10-31T00:00:00Z",
        error_code: "STORE_ERROR",
      },
    ];

    render(
      <DocumentLibrary
        documents={documents}
        loading={false}
        error={null}
        deletingId={null}
        onDelete={vi.fn()}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByText("error: STORE_ERROR")).toBeInTheDocument();
  });
});
