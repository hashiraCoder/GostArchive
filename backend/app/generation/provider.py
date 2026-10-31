"""Pluggable LLM provider interface and factory for GhostArchive."""

from __future__ import annotations

import logging
from typing import Any, Protocol

import httpx

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.generation.ollama_client import OllamaClient

logger = logging.getLogger("ghostarchive.provider")


class LLMProvider(Protocol):
    """Protocol for model text generation providers."""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a system prompt and user prompt, returning the model's text response."""
        ...

    @property
    def model_name(self) -> str:
        """The identifier of the active model."""
        ...


class ExternalLLMProvider:
    """
    Adapter for external OpenAI-compatible or cloud model APIs.

    Used when a user explicitly configures an external provider
    (e.g., Gemini or OpenAI-compatible service) while preserving
    the same structured generation contract.
    """

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client
        self._api_key = settings.external_api_key or ""
        self._base_url = (settings.external_api_base_url or "https://api.openai.com/v1").rstrip("/")
        self._model = settings.external_model or "gemini-2.5-flash"

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise GhostArchiveException(
                ErrorCode.VALIDATION_ERROR,
                "External LLM provider selected but no API key was provided.",
                400,
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        try:
            if self._client is None:
                with httpx.Client(timeout=self._settings.ollama_timeout_seconds) as client:
                    response = client.post(
                        f"{self._base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
            else:
                response = self._client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )

            if response.status_code in (401, 403):
                raise GhostArchiveException(
                    ErrorCode.MODEL_UNAVAILABLE,
                    "Authentication failed with external LLM provider.",
                    503,
                )
            if response.status_code == 429:
                raise GhostArchiveException(
                    ErrorCode.MODEL_UNAVAILABLE,
                    "External LLM provider rate limit exceeded.",
                    503,
                    retryable=True,
                )
            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise GhostArchiveException(
                    ErrorCode.GENERATION_FAILED,
                    "External provider returned empty choices.",
                    502,
                )
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise GhostArchiveException(
                    ErrorCode.GENERATION_FAILED,
                    "External provider returned empty content.",
                    502,
                )
            return content
        except GhostArchiveException:
            raise
        except (httpx.ConnectError, httpx.RequestError) as exc:
            raise GhostArchiveException(
                ErrorCode.MODEL_UNAVAILABLE,
                "External LLM provider is unreachable.",
                503,
                retryable=True,
            ) from exc
        except httpx.TimeoutException as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_TIMEOUT,
                "External LLM provider timed out during generation.",
                504,
                retryable=True,
            ) from exc
        except Exception as exc:
            raise GhostArchiveException(
                ErrorCode.GENERATION_FAILED,
                "Failed to parse response from external LLM provider.",
                502,
            ) from exc


def get_llm_provider(
    settings: Settings,
    client: httpx.Client | None = None,
) -> LLMProvider:
    """
    Factory creating the configured LLM provider.

    Defaults strictly to local Ollama (100% offline and private).
    Only instantiates ExternalLLMProvider when explicitly opted-in
    with a non-empty API key.
    """
    provider_name = (settings.llm_provider or "ollama").strip().lower()

    if provider_name == "external":
        if settings.external_api_key:
            return ExternalLLMProvider(settings, client=client)
        logger.warning(
            "GHOSTARCHIVE_LLM_PROVIDER is 'external' but no API key was configured. "
            "Falling back to local Ollama provider."
        )

    return OllamaClient(settings, client=client)
