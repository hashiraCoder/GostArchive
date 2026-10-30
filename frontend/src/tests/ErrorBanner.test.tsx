import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ErrorBanner } from "../components/ErrorBanner";

describe("ErrorBanner component", () => {
  it("renders error code and message", () => {
    const error = {
      code: "MODEL_UNAVAILABLE",
      message: "The local language model is not running.",
      retryable: false,
    };
    render(<ErrorBanner error={error} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("MODEL_UNAVAILABLE")).toBeInTheDocument();
    expect(
      screen.getByText("The local language model is not running."),
    ).toBeInTheDocument();
  });

  it("renders retry button when retryable is true and onRetry is provided", () => {
    const error = {
      code: "STORE_ERROR",
      message: "Temporary storage lock",
      retryable: true,
    };
    const onRetry = vi.fn();
    render(<ErrorBanner error={error} onRetry={onRetry} />);
    const retryBtn = screen.getByRole("button", { name: /try again/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("omits retry button when retryable is false", () => {
    const error = {
      code: "VALIDATION_ERROR",
      message: "Invalid field",
      retryable: false,
    };
    render(<ErrorBanner error={error} onRetry={vi.fn()} />);
    expect(
      screen.queryByRole("button", { name: /try again/i }),
    ).not.toBeInTheDocument();
  });
});
