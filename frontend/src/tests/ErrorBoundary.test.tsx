import React, { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ErrorBoundary } from "../components/ErrorBoundary";

const ProblemChild: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error("Simulated component crash");
  }
  return <div>Component rendered safely</div>;
};

const Harness: React.FC = () => {
  const [hasError, setHasError] = useState(true);
  return (
    <ErrorBoundary onReset={() => setHasError(false)}>
      <ProblemChild shouldThrow={hasError} />
    </ErrorBoundary>
  );
};

describe("ErrorBoundary", () => {
  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Safe content")).toBeInTheDocument();
  });

  it("catches errors in children and displays fallback UI", () => {
    // Suppress console.error in test output for intentional error
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Rendering Error")).toBeInTheDocument();
    expect(
      screen.getByText("Something went wrong in the workspace UI"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Simulated component crash"),
    ).toBeInTheDocument();

    spy.mockRestore();
  });

  it("resets state when Try Again is clicked", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(<Harness />);
    expect(screen.getByRole("alert")).toBeInTheDocument();

    const tryAgainBtn = screen.getByRole("button", { name: /try again/i });
    fireEvent.click(tryAgainBtn);

    expect(screen.getByText("Component rendered safely")).toBeInTheDocument();

    spy.mockRestore();
  });
});
