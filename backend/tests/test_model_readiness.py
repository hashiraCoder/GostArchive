"""
Regression tests for model readiness, Ollama connectivity, error categorization,
and readiness/chat decoupling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.generation.ollama_client import OllamaClient


def test_1_ollama_unreachable(client: TestClient, temp_settings: Settings) -> None:
    """1. Ollama unreachable reports accurate unavailable states and retryable connection error."""
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")),
    ):
        res = client.get("/api/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["overall"] == "unavailable"
        deps = data["dependencies"]
        assert deps["ollama_service"]["status"] == "unavailable"
        assert deps["model_available"]["status"] == "unavailable"
        assert deps["model_inference"]["status"] == "unavailable"
        assert deps["ollama"]["status"] == "unavailable"

    mock_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: (_ for _ in ()).throw(httpx.ConnectError("Connection refused"))
        )
    )
    ollama = OllamaClient(temp_settings, client=mock_client)
    with pytest.raises(GhostArchiveException) as exc:
        ollama.chat("system", "user")
    assert exc.value.code == ErrorCode.MODEL_UNAVAILABLE
    assert exc.value.status_code == 503
    assert exc.value.retryable is True
    assert "unreachable" in exc.value.message.lower()


def test_2_ollama_reachable_but_model_missing(client: TestClient, temp_settings: Settings) -> None:
    """2. Ollama reachable but model missing returns degraded readiness and MODEL_NOT_FOUND."""
    mock_tags = httpx.Response(
        status_code=200,
        json={"models": [{"name": "other-model:latest"}]},
        request=httpx.Request("GET", "http://127.0.0.1:11434/api/tags"),
    )
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_tags),
    ):
        res = client.get("/api/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["overall"] == "degraded"
        deps = data["dependencies"]
        assert deps["ollama_service"]["status"] == "ready"
        assert deps["model_available"]["status"] == "degraded"
        assert "not found" in deps["model_available"]["message"].lower()

    # Ollama returns 404 when model is missing
    mock_chat = httpx.Response(
        status_code=404,
        json={"error": "model 'gemma3:1b' not found, try pulling it first"},
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/chat"),
    )
    mock_client = httpx.Client(transport=httpx.MockTransport(lambda req: mock_chat))
    ollama = OllamaClient(temp_settings, client=mock_client)
    with pytest.raises(GhostArchiveException) as exc:
        ollama.chat("system", "user")
    assert exc.value.code == ErrorCode.MODEL_NOT_FOUND
    assert exc.value.status_code == 503
    assert exc.value.retryable is False  # Retrying cannot pull the model
    assert "ollama pull" in exc.value.message


def test_3_ollama_reachable_and_model_available(client: TestClient) -> None:
    """3. Ollama reachable and model available reports ready across all checks."""
    mock_tags = httpx.Response(
        status_code=200,
        json={"models": [{"name": "gemma3:1b"}]},
        request=httpx.Request("GET", "http://127.0.0.1:11434/api/tags"),
    )
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_tags),
    ):
        res = client.get("/api/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["overall"] == "ready"
        deps = data["dependencies"]
        assert deps["ollama_service"]["status"] == "ready"
        assert deps["model_available"]["status"] == "ready"
        assert deps["model_inference"]["status"] == "ready"


def test_4_model_generation_timeout(temp_settings: Settings) -> None:
    """4. Generation timeout raises GENERATION_TIMEOUT with 504 and retryable True."""
    mock_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: (_ for _ in ()).throw(httpx.ReadTimeout("Timed out"))
        )
    )
    ollama = OllamaClient(temp_settings, client=mock_client)
    with pytest.raises(GhostArchiveException) as exc:
        ollama.chat("system", "user")
    assert exc.value.code == ErrorCode.GENERATION_TIMEOUT
    assert exc.value.status_code == 504
    assert exc.value.retryable is True
    assert "timed out" in exc.value.message.lower()


def test_5_model_generation_failure(temp_settings: Settings) -> None:
    """5. Model runtime failure (500 / OOM) raises GENERATION_FAILED with 502."""
    mock_500 = httpx.Response(
        status_code=500,
        json={"error": "CUDA out of memory"},
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/chat"),
    )
    mock_client = httpx.Client(transport=httpx.MockTransport(lambda req: mock_500))
    ollama = OllamaClient(temp_settings, client=mock_client)
    with pytest.raises(GhostArchiveException) as exc:
        ollama.chat("system", "user")
    assert exc.value.code == ErrorCode.GENERATION_FAILED
    assert exc.value.status_code == 502
    assert "CUDA out of memory" in exc.value.message

    # Empty content
    mock_empty = httpx.Response(
        status_code=200,
        json={"message": {"content": ""}},
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/chat"),
    )
    empty_transport = httpx.MockTransport(lambda req: mock_empty)
    ollama_empty = OllamaClient(temp_settings, client=httpx.Client(transport=empty_transport))
    with pytest.raises(GhostArchiveException) as exc_empty:
        ollama_empty.chat("system", "user")
    assert exc_empty.value.code == ErrorCode.GENERATION_FAILED
    assert exc_empty.value.status_code == 502


def test_6_embedding_service_failure(client: TestClient) -> None:
    """6. Embedding package uninstalled sets embedding_service to unavailable."""
    with patch("importlib.util.find_spec", return_value=None):
        res = client.get("/api/ready")
        data = res.json()
        assert data["dependencies"]["embedding_service"]["status"] == "unavailable"
        assert data["dependencies"]["embedding_model"]["status"] == "unavailable"


def test_7_api_ready_reporting_accurate_component_states(client: TestClient) -> None:
    """7. /api/ready exposes the 5 distinct health states and supports active inference probing."""
    mock_tags = httpx.Response(
        status_code=200,
        json={"models": [{"name": "gemma3:1b"}]},
        request=httpx.Request("GET", "http://127.0.0.1:11434/api/tags"),
    )
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_tags),
    ):
        res = client.get("/api/ready")
        data = res.json()
        deps = data["dependencies"]
        assert "ollama_service" in deps
        assert "model_available" in deps
        assert "model_inference" in deps
        assert "embedding_service" in deps
        assert "document_storage" in deps

    # Test active probe ?check_inference=true
    mock_chat_ok = httpx.Response(
        status_code=200,
        json={"message": {"content": "OK"}},
        request=httpx.Request("POST", "http://127.0.0.1:11434/api/chat"),
    )
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_tags),
        patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_chat_ok),
    ):
        res_probe = client.get("/api/ready", params={"check_inference": "true"})
        assert res_probe.status_code == 200
        data_probe = res_probe.json()
        assert data_probe["dependencies"]["model_inference"]["status"] == "ready"
        assert "latency < 5s" in data_probe["dependencies"]["model_inference"]["message"]


def test_8_api_chat_returns_correct_error_code_and_http_status(
    client: TestClient, monkeypatch
) -> None:
    """8. /api/chat returns distinct HTTP statuses: 503, 504 (timeout), 502 (generation error)."""
    # Force search to return evidence so ask_question executes the LLM step
    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "sample text",
            "start_char": 0,
            "end_char": 10,
            "score": 0.9,
        }
    ]
    monkeypatch.setattr(
        "app.services.chat_service.search_documents",
        lambda *args, **kwargs: fake_evidence,
    )

    # 8a: Connect error -> 503 MODEL_UNAVAILABLE
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Ollama down")):
        res_503 = client.post("/api/chat", json={"question": "What is here?"})
        assert res_503.status_code == 503
        assert res_503.json()["error"]["code"] == "MODEL_UNAVAILABLE"
        assert res_503.json()["error"]["retryable"] is True

    # 8b: Model missing (404) -> 503 MODEL_NOT_FOUND (non-retryable)
    mock_404 = httpx.Response(
        404,
        json={"error": "model 'gemma3:1b' not found"},
        request=httpx.Request("POST", "url"),
    )
    with patch("httpx.Client.post", return_value=mock_404):
        res_missing = client.post("/api/chat", json={"question": "What is here?"})
        assert res_missing.status_code == 503
        assert res_missing.json()["error"]["code"] == "MODEL_NOT_FOUND"
        assert res_missing.json()["error"]["retryable"] is False
        assert "ollama pull" in res_missing.json()["error"]["message"]

    # 8c: Timeout -> 504 GENERATION_TIMEOUT
    with patch("httpx.Client.post", side_effect=httpx.ReadTimeout("Generation timed out")):
        res_504 = client.post("/api/chat", json={"question": "What is here?"})
        assert res_504.status_code == 504
        assert res_504.json()["error"]["code"] == "GENERATION_TIMEOUT"
        assert res_504.json()["error"]["retryable"] is True

    # 8d: Runner crash -> 502 GENERATION_FAILED
    mock_500 = httpx.Response(
        500,
        json={"error": "runner terminated"},
        request=httpx.Request("POST", "url"),
    )
    with patch("httpx.Client.post", return_value=mock_500):
        res_502 = client.post("/api/chat", json={"question": "What is here?"})
        assert res_502.status_code == 502
        assert res_502.json()["error"]["code"] == "GENERATION_FAILED"


def test_9_documents_remain_ready_when_ollama_unavailable(client: TestClient) -> None:
    """9. Documents remain ready, searchable, and intact even when Ollama is completely offline."""
    # Ingest document
    file_payload = ("historical_journal.txt", b"In August 1914, mobilization began.", "text/plain")
    upload_res = client.post(
        "/api/documents",
        files={"file": file_payload},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document"]["id"]
    assert upload_res.json()["document"]["status"] == "ready"

    # Now simulate Ollama completely offline
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Ollama connection refused")):
        # 1. Document metadata is still ready
        doc_detail = client.get(f"/api/documents/{doc_id}")
        assert doc_detail.status_code == 200
        assert doc_detail.json()["status"] == "ready"

        # 2. Search works independently of Ollama
        search_res = client.post("/api/search", json={"query": "mobilization"})
        assert search_res.status_code == 200
        assert search_res.json()["total"] >= 1
        assert "mobilization" in search_res.json()["items"][0]["text"]

        # 3. Chat fails with exact MODEL_UNAVAILABLE error
        chat_res = client.post("/api/chat", json={"question": "When did mobilization begin?"})
        assert chat_res.status_code == 503
        assert chat_res.json()["error"]["code"] == "MODEL_UNAVAILABLE"

        # 4. Document is STILL ready
        doc_after_chat = client.get(f"/api/documents/{doc_id}")
        assert doc_after_chat.status_code == 200
        assert doc_after_chat.json()["status"] == "ready"
