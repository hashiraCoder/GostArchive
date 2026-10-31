"""Ollama HTTP client."""

from __future__ import annotations

import contextlib
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
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise GhostArchiveException(
                ErrorCode.MODEL_UNAVAILABLE,
                (
                    f"The local Ollama service is unreachable at {self._settings.ollama_base_url}. "
                    "Ensure the service is running (`ollama serve`)."
                ),
                503,
                retryable=True,
            ) from exc
        except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_TIMEOUT,
                (
                    f"Model generation timed out after {self._settings.ollama_timeout_seconds}s. "
                    "The local hardware may be constrained or the context is too large."
                ),
                504,
                retryable=True,
            ) from exc
        except httpx.RequestError as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                f"Communication error with local Ollama service: {exc!s}",
                502,
                retryable=True,
            ) from exc

        # Handle HTTP error status codes from Ollama with accurate categorization
        if response.status_code == 404:
            error_detail = ""
            with contextlib.suppress(Exception):
                error_detail = response.json().get("error", "")
            msg = (
                f"Configured model '{self.model_name}' is not installed in local Ollama. "
                f"Run: ollama pull {self.model_name}"
            )
            if error_detail:
                msg += f" (Ollama: {error_detail})"
            raise GhostArchiveException(
                ErrorCode.MODEL_NOT_FOUND,
                msg,
                503,
                retryable=False,  # Retrying will not pull the model
            )

        if response.status_code == 500:
            error_detail = ""
            with contextlib.suppress(Exception):
                error_detail = response.json().get("error", "")
            msg = "Ollama model execution failed."
            if error_detail:
                msg += f" (Ollama: {error_detail})"
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                msg,
                502,
                retryable=True,
            )

        if response.status_code == 503:
            raise GhostArchiveException(
                ErrorCode.MODEL_UNAVAILABLE,
                "The local Ollama service is overloaded or unavailable.",
                503,
                retryable=True,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                f"Ollama returned HTTP {response.status_code}: {exc!s}",
                502,
                retryable=True,
            ) from exc

        try:
            body = response.json()
        except (ValueError, TypeError) as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                "The local model returned an invalid non-JSON response.",
                502,
                retryable=True,
            ) from exc

        content = body.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                "The local model returned an empty response.",
                502,
                retryable=True,
            )
        return content
