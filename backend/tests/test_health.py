"""
Tests for health and readiness routes and error envelopes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    """GET /api/health returns 200 with ok status and version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_version"] == "0.1.0"


def test_health_no_model_call(client: TestClient) -> None:
    """GET /api/health succeeds even if Ollama is completely unreachable."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Ollama down")):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_ready_structure(client: TestClient) -> None:
    """GET /api/ready returns the expected schema keys."""
    response = client.get("/api/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "overall" in data
    assert "dependencies" in data
    deps = data["dependencies"]
    assert "database" in deps
    assert "chroma" in deps
    assert "embedding_model" in deps
    assert "ollama" in deps
    for dep in deps.values():
        assert "status" in dep
        assert dep["status"] in ("ready", "degraded", "unavailable")


def test_ready_all_up(client: TestClient) -> None:
    """GET /api/ready returns overall: ready (200) when all dependencies are ready."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"models": [{"name": "gemma3:1b"}]},
        request=httpx.Request("GET", "http://127.0.0.1:11434/api/tags"),
    )
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp),
    ):
        response = client.get("/api/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["overall"] == "ready"
        assert data["dependencies"]["ollama"]["status"] == "ready"
        assert data["dependencies"]["embedding_model"]["status"] == "ready"
        assert data["dependencies"]["database"]["status"] == "ready"
        assert data["dependencies"]["chroma"]["status"] == "ready"


def test_ready_ollama_unavailable(client: TestClient) -> None:
    """GET /api/ready returns 503 and overall: unavailable when Ollama is offline."""
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")),
    ):
        response = client.get("/api/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["overall"] == "unavailable"
        assert data["dependencies"]["ollama"]["status"] == "unavailable"


def test_ready_ollama_degraded(client: TestClient) -> None:
    """GET /api/ready returns 200 with degraded status if model is missing in Ollama."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"models": [{"name": "other-model:latest"}]},
        request=httpx.Request("GET", "http://127.0.0.1:11434/api/tags"),
    )
    with (
        patch("importlib.util.find_spec", return_value=True),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp),
    ):
        response = client.get("/api/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["overall"] == "degraded"
        assert data["dependencies"]["ollama"]["status"] == "degraded"


def test_error_envelope_404(client: TestClient) -> None:
    """404 Not Found returns the standardized ErrorEnvelope shape."""
    response = client.get("/api/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
    assert "retryable" in data["error"]


def test_cors_allowed_origin(client: TestClient) -> None:
    """Requests from allowed local Vite origin receive CORS headers."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_rejected_origin(client: TestClient) -> None:
    """Requests from unauthorized origins do not receive CORS headers."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://malicious-external-site.com"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
