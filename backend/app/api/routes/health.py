"""
Health and readiness API routes.
"""

from __future__ import annotations

import importlib.util
import logging
import sqlite3
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings, get_settings
from app.schemas.health import (
    DependencyDetail,
    DependencyStatus,
    HealthResponse,
    ReadyResponse,
)

logger = logging.getLogger("ghostarchive.health")

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """
    Returns process health status only.
    Must not perform heavy I/O, database initialization, or AI model calls.
    """
    return HealthResponse(status="ok", app_version=settings.app_version)


def check_database(settings: Settings) -> DependencyDetail:
    """Check if SQLite database file/directory is accessible and tables exist."""
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(settings.db_path, timeout=2.0)
        try:
            conn.execute("SELECT 1")
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
                ).fetchall()
            }
            if not {"documents", "document_chunks"}.issubset(tables):
                return DependencyDetail(
                    status=DependencyStatus.ready,
                    message="Database accessible (schema will auto-initialize on first write)",
                )
        finally:
            conn.close()
        return DependencyDetail(status=DependencyStatus.ready)
    except Exception as exc:
        logger.warning("Database check failed: %s", type(exc).__name__)
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Database storage path inaccessible",
        )


def check_chroma(settings: Settings) -> DependencyDetail:
    """Check if ChromaDB persistent storage directory is accessible and operational."""
    try:
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        from app.retrieval.vector_store import ChromaVectorStore

        store = ChromaVectorStore(settings)
        _ = store.collection.count()
        return DependencyDetail(status=DependencyStatus.ready)
    except Exception as exc:
        logger.warning("Chroma path check failed: %s", type(exc).__name__)
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Chroma vector store directory inaccessible",
        )


def check_document_storage(
    settings: Settings,
) -> tuple[DependencyDetail, DependencyDetail, DependencyDetail]:
    """Check both SQLite database and ChromaDB vector store directories."""
    db_detail = check_database(settings)
    chroma_detail = check_chroma(settings)

    if (
        db_detail.status == DependencyStatus.unavailable
        or chroma_detail.status == DependencyStatus.unavailable
    ):
        combined_status = DependencyStatus.unavailable
        msg = f"Storage error (SQLite: {db_detail.status}, Chroma: {chroma_detail.status})"
    elif (
        db_detail.status == DependencyStatus.degraded
        or chroma_detail.status == DependencyStatus.degraded
    ):
        combined_status = DependencyStatus.degraded
        msg = f"Storage degraded (SQLite: {db_detail.status}, Chroma: {chroma_detail.status})"
    else:
        combined_status = DependencyStatus.ready
        msg = "SQLite and ChromaDB storage accessible and operational"

    storage_detail = DependencyDetail(status=combined_status, message=msg)
    return storage_detail, db_detail, chroma_detail


def check_embedding_model(settings: Settings) -> DependencyDetail:
    """
    Check if the embedding package is installed and whether weights are cached locally.
    Does not initiate a heavy download on health check.
    """
    import os
    from pathlib import Path

    spec = importlib.util.find_spec("sentence_transformers")
    if spec is None:
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message="sentence-transformers package not installed in environment",
        )

    hf_home = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
    hub_dir = Path(hf_home) / "hub"
    model_slug = "models--" + settings.embedding_model.replace("/", "--")
    cached = (hub_dir / model_slug).exists() if hub_dir.exists() else False

    if cached or os.environ.get("HF_HUB_OFFLINE") == "1":
        return DependencyDetail(
            status=DependencyStatus.ready,
            message=f"Model ready ({settings.embedding_model})",
        )
    return DependencyDetail(
        status=DependencyStatus.degraded,
        message=(
            f"Library installed ({settings.embedding_model}). "
            "Model weights will download on first document import."
        ),
    )


def check_embedding_service(settings: Settings) -> DependencyDetail:
    """Check if local embedding provider and sentence-transformers model are ready."""
    return check_embedding_model(settings)


async def check_ollama_connectivity(
    settings: Settings,
) -> tuple[DependencyDetail, DependencyDetail, DependencyDetail]:
    """
    Check Ollama daemon reachability (ollama_service) and model existence (model_available)
    via GET /api/tags with a lightweight 2.0s timeout.
    """
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    target_model = settings.ollama_model
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                ollama_service = DependencyDetail(
                    status=DependencyStatus.ready,
                    message=f"Ollama daemon reachable at {settings.ollama_base_url}",
                )

                # Check for exact or base model match (e.g., "gemma3:1b" vs "gemma3:1b-instruct")
                model_found = any(
                    target_model == m
                    or m.startswith(f"{target_model}:")
                    or target_model.startswith(f"{m}:")
                    for m in models
                    if m
                )
                if model_found:
                    model_available = DependencyDetail(
                        status=DependencyStatus.ready,
                        message=f"Model '{target_model}' installed in local Ollama",
                    )
                    ollama_summary = DependencyDetail(status=DependencyStatus.ready)
                else:
                    model_available = DependencyDetail(
                        status=DependencyStatus.degraded,
                        message=f"Model '{target_model}' not found in local Ollama models",
                    )
                    ollama_summary = DependencyDetail(
                        status=DependencyStatus.degraded,
                        message=f"Model '{target_model}' not found in local Ollama models",
                    )
                return ollama_service, model_available, ollama_summary
            service_detail = DependencyDetail(
                status=DependencyStatus.unavailable,
                message=f"Ollama returned unexpected status {resp.status_code}",
            )
            model_detail = DependencyDetail(
                status=DependencyStatus.unavailable,
                message="Cannot verify model availability: Ollama service error",
            )
            return service_detail, model_detail, service_detail
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
        logger.debug("Ollama connectivity check failed: %s", type(exc).__name__)
        service_detail = DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Local Ollama service unreachable",
        )
        model_detail = DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Cannot verify model availability: Ollama daemon is offline",
        )
        return service_detail, model_detail, service_detail


async def check_ollama(settings: Settings) -> DependencyDetail:
    """Legacy helper returning unified Ollama dependency status for backward compatibility."""
    _, _, summary = await check_ollama_connectivity(settings)
    return summary


async def check_model_inference(
    settings: Settings,
    model_status: DependencyStatus,
    *,
    probe_inference: bool = False,
) -> DependencyDetail:
    """
    Check model inference capability.
    Avoids expensive model generation requests during routine health polling.
    When probe_inference=True (via ?check_inference=true), performs a lightweight test generation
    with an explicit strict timeout of 5.0s.
    """
    if model_status == DependencyStatus.unavailable:
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Inference unavailable: Ollama service is unreachable",
        )
    if model_status == DependencyStatus.degraded:
        return DependencyDetail(
            status=DependencyStatus.degraded,
            message=(
                f"Inference unavailable: model '{settings.ollama_model}' not found in local Ollama"
            ),
        )

    if not probe_inference:
        return DependencyDetail(
            status=DependencyStatus.ready,
            message="Model available for inference (pass ?check_inference=true for active probe)",
        )

    # Active inference probe
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "user", "content": "respond with OK"}],
        "stream": False,
        "options": {"num_predict": 5},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return DependencyDetail(
                    status=DependencyStatus.ready,
                    message="Active inference probe succeeded (latency < 5s)",
                )
            return DependencyDetail(
                status=DependencyStatus.unavailable,
                message=f"Active inference probe returned HTTP {resp.status_code}",
            )
    except httpx.TimeoutException:
        return DependencyDetail(
            status=DependencyStatus.degraded,
            message="Active inference probe timed out (cost: 5s timeout exceeded)",
        )
    except Exception as exc:
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message=f"Active inference probe failed: {exc!s}",
        )


@router.get("/ready", response_model=ReadyResponse)
async def get_ready(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    check_inference: bool = False,
) -> ReadyResponse:
    """
    Checks per-dependency status:
    - ollama_service: reachable HTTP daemon
    - model_available: configured model present in Ollama tags
    - model_inference: lightweight ready or active probe (?check_inference=true)
    - embedding_service: sentence-transformers ready
    - document_storage: SQLite and Chroma persistence accessible
    Also provides backward-compatible keys: database, chroma, embedding_model, ollama.
    Sets HTTP 503 if any critical dependency is unavailable, otherwise 200.
    """
    storage_detail, db_detail, chroma_detail = check_document_storage(settings)
    embedding_detail = check_embedding_service(settings)
    ollama_service, model_available, ollama_summary = await check_ollama_connectivity(settings)
    inference_detail = await check_model_inference(
        settings, model_available.status, probe_inference=check_inference
    )

    dependencies = {
        # Distinct health states
        "ollama_service": ollama_service,
        "model_available": model_available,
        "model_inference": inference_detail,
        "embedding_service": embedding_detail,
        "document_storage": storage_detail,
        # Backward-compatible keys
        "database": db_detail,
        "chroma": chroma_detail,
        "embedding_model": embedding_detail,
        "ollama": ollama_summary,
    }

    # Overall calculation: if storage, embedding, or ollama service is unavailable -> 503
    critical_statuses = [
        db_detail.status,
        chroma_detail.status,
        ollama_service.status,
    ]
    if DependencyStatus.unavailable in critical_statuses:
        overall = DependencyStatus.unavailable
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif DependencyStatus.degraded in [
        dep.status for dep in dependencies.values()
    ] or DependencyStatus.unavailable in [dep.status for dep in dependencies.values()]:
        overall = DependencyStatus.degraded
        response.status_code = status.HTTP_200_OK
    else:
        overall = DependencyStatus.ready
        response.status_code = status.HTTP_200_OK

    return ReadyResponse(overall=overall, dependencies=dependencies)
