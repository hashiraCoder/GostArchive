import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { StatusIndicator } from "../components/StatusIndicator";
import type { ReadyResponse } from "../api/health";

describe("StatusIndicator component", () => {
  const mockAllReady: ReadyResponse = {
    overall: "ready",
    dependencies: {
      database: { status: "ready" },
      chroma: { status: "ready" },
      embedding_model: { status: "ready" },
      ollama: { status: "ready" },
    },
  };

  it("renders loading indicator when loading without cached data", () => {
    render(<StatusIndicator readyData={null} loading={true} error={null} />);
    expect(screen.getByText(/checking local archive services/i)).toBeInTheDocument();
  });

  it("renders all four dependency badges with ready status", () => {
    render(<StatusIndicator readyData={mockAllReady} loading={false} error={null} />);
    expect(screen.getByLabelText(/sqlite db: ready/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/chroma store: ready/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/embeddings: ready/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ollama model: ready/i)).toBeInTheDocument();
  });

  it("renders offline status accurately when Ollama is unavailable", () => {
    const mockDegraded: ReadyResponse = {
      overall: "unavailable",
      dependencies: {
        database: { status: "ready" },
        chroma: { status: "ready" },
        embedding_model: { status: "ready" },
        ollama: { status: "unavailable", message: "Ollama service offline" },
      },
    };
    render(<StatusIndicator readyData={mockDegraded} loading={false} error={null} />);
    const badge = screen.getByLabelText(/ollama model: offline/i);
    expect(badge).toBeInTheDocument();
    expect(screen.queryByLabelText(/ollama model: ready/i)).not.toBeInTheDocument();
  });

  it("renders degraded status accurately when a dependency is incomplete", () => {
    const mockDegraded: ReadyResponse = {
      overall: "degraded",
      dependencies: {
        database: { status: "ready" },
        chroma: { status: "ready" },
        embedding_model: {
          status: "degraded",
          message: "Embedding model is not loaded",
        },
        ollama: { status: "ready" },
      },
    };
    render(<StatusIndicator readyData={mockDegraded} loading={false} error={null} />);
    expect(screen.getByLabelText(/embeddings: degraded/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ollama model: ready/i)).toBeInTheDocument();
  });

  it("renders error banner when API error occurs", () => {
    const mockError = {
      code: "SERVICE_UNREACHABLE",
      message: "Connection failed",
      retryable: true,
    };
    render(<StatusIndicator readyData={null} loading={false} error={mockError} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("SERVICE_UNREACHABLE")).toBeInTheDocument();
  });
});
