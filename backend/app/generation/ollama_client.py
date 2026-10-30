"""Ollama HTTP client."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException


class OllamaClient:
    """Small client for local Ollama structured chat responses."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client

    @property
    def model_name(self) -> str:
        return self._settings.ollama_model

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self._settings.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1},
        }
        try:
            if self._client is None:
                with httpx.Client(timeout=self._settings.ollama_timeout_seconds) as client:
                    response = client.post(
                        f"{self._settings.ollama_base_url.rstrip('/')}/api/chat",
                        json=payload,
                    )
            else:
                response = self._client.post(
                    f"{self._settings.ollama_base_url.rstrip('/')}/api/chat",
                    json=payload,
                )
            if response.status_code in (404, 500, 503):
                raise GhostArchiveException(
                    ErrorCode.MODEL_UNAVAILABLE,
                    "The configured local Ollama model is unavailable.",
                    503,
                    retryable=True,
                )
            response.raise_for_status()
            body = response.json()
            content = body.get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                raise GhostArchiveException(
                    ErrorCode.GENERATION_FAILED,
                    "The local model returned an empty response.",
                    502,
                    retryable=True,
                )
            return content
        except GhostArchiveException:
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
            raise GhostArchiveException(
                ErrorCode.MODEL_UNAVAILABLE,
                "The local Ollama service is unavailable.",
                503,
                retryable=True,
            ) from exc
        except (httpx.HTTPStatusError, ValueError, TypeError) as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                "The local model returned an invalid response.",
                502,
                retryable=True,
            ) from exc
