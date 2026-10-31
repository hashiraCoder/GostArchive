"""Tests for the pluggable LLM provider interface and factory."""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.generation.ollama_client import OllamaClient
from app.generation.provider import ExternalLLMProvider, get_llm_provider


def test_default_provider_is_ollama(temp_settings: Settings) -> None:
    provider = get_llm_provider(temp_settings)
    assert isinstance(provider, OllamaClient)
    assert provider.model_name == temp_settings.ollama_model


def test_external_provider_without_key_falls_back_to_ollama(temp_settings: Settings) -> None:
    settings = temp_settings.model_copy(
        update={"llm_provider": "external", "external_api_key": None}
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, OllamaClient)


def test_external_provider_with_key_returns_external_provider(temp_settings: Settings) -> None:
    settings = temp_settings.model_copy(
        update={
            "llm_provider": "external",
            "external_api_key": "test-key-123",
            "external_model": "gemini-2.5-flash",
        }
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, ExternalLLMProvider)
    assert provider.model_name == "gemini-2.5-flash"


def test_external_provider_chat_mock(temp_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("Authorization") == "Bearer secret-token"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": '{"answer": "External answer", "cited_chunk_ids": []}',
                        }
                    }
                ]
            },
        )

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = temp_settings.model_copy(
        update={
            "llm_provider": "external",
            "external_api_key": "secret-token",
            "external_model": "test-model",
            "external_api_base_url": "https://custom-api.com/v1",
        }
    )
    provider = ExternalLLMProvider(settings, client=mock_client)
    res = provider.chat("system prompt", "user prompt")
    assert "External answer" in res


def test_external_provider_auth_error_is_explicit(temp_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Unauthorized"})

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = temp_settings.model_copy(
        update={
            "llm_provider": "external",
            "external_api_key": "bad-key",
        }
    )
    provider = ExternalLLMProvider(settings, client=mock_client)
    with pytest.raises(GhostArchiveException) as exc:
        provider.chat("system", "user")
    assert exc.value.code == ErrorCode.MODEL_UNAVAILABLE
