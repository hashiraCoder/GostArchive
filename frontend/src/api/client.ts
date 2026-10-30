/**
 * GhostArchive typed API client.
 *
 * All network requests must flow through apiFetch.
 * Never call fetch() directly from inside components.
 */

export interface ApiError {
  code: string;
  message: string;
  retryable: boolean;
}

export class ApiException extends Error {
  constructor(
    public readonly status: number,
    public readonly error: ApiError,
  ) {
    super(error.message);
    this.name = "ApiException";
  }
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const normalizedPath = path.startsWith("/api")
    ? path
    : `/api${path.startsWith("/") ? "" : "/"}${path}`;

  let response: Response;
  try {
    response = await fetch(normalizedPath, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options?.headers ?? {}),
      },
    });
  } catch (_err) {
    throw new ApiException(0, {
      code: "SERVICE_UNREACHABLE",
      message: "Cannot reach local GhostArchive service at 127.0.0.1:8000.",
      retryable: true,
    });
  }

  if (!response.ok) {
    let errorDetail: ApiError;
    try {
      const data = await response.json();
      if (data && typeof data === "object" && "error" in data && data.error) {
        errorDetail = {
          code: String(data.error.code || "INTERNAL_ERROR"),
          message: String(data.error.message || "An error occurred."),
          retryable: Boolean(data.error.retryable),
        };
      } else {
        errorDetail = {
          code: "INTERNAL_ERROR",
          message: `Request failed with status ${response.status}`,
          retryable: response.status >= 500,
        };
      }
    } catch {
      errorDetail = {
        code: "INTERNAL_ERROR",
        message: `HTTP ${response.status} ${response.statusText}`,
        retryable: response.status >= 500,
      };
    }
    throw new ApiException(response.status, errorDetail);
  }

  if (
    response.status === 204 ||
    response.headers?.get?.("content-length") === "0"
  ) {
    return undefined as unknown as T;
  }

  if (typeof response.text === "function") {
    const text = await response.text();
    if (!text.trim()) {
      return undefined as unknown as T;
    }
    return JSON.parse(text) as T;
  }

  return response.json() as Promise<T>;
}
