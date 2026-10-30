import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiFetch, ApiException } from "../api/client";

describe("apiFetch client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON on successful 200 response", async () => {
    const mockData = { status: "ok", app_version: "0.1.0" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    } as Response);

    const result = await apiFetch<{ status: string }>("/health");
    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/health",
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("throws ApiException with parsed ErrorEnvelope on 404 response", async () => {
    const errorBody = {
      error: {
        code: "NOT_FOUND",
        message: "Endpoint not found",
        retryable: false,
      },
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => errorBody,
    } as Response);

    await expect(apiFetch("/nonexistent")).rejects.toThrow(ApiException);
    try {
      await apiFetch("/nonexistent");
    } catch (err) {
      const apiErr = err as ApiException;
      expect(apiErr.status).toBe(404);
      expect(apiErr.error.code).toBe("NOT_FOUND");
    }
  });

  it("throws ApiException with SERVICE_UNREACHABLE on network failure", async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(apiFetch("/health")).rejects.toThrow(ApiException);
    try {
      await apiFetch("/health");
    } catch (err) {
      const apiErr = err as ApiException;
      expect(apiErr.status).toBe(0);
      expect(apiErr.error.code).toBe("SERVICE_UNREACHABLE");
      expect(apiErr.error.retryable).toBe(true);
    }
  });
});
