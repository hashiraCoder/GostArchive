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
    """Check if SQLite database file/directory is accessible."""
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        # Attempt connection test
        conn = sqlite3.connect(settings.db_path, timeout=2.0)
        try:
            conn.execute("SELECT 1")
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
    """Check if ChromaDB persistent storage directory is accessible."""
    try:
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        return DependencyDetail(status=DependencyStatus.ready)
    except Exception as exc:
        logger.warning("Chroma path check failed: %s", type(exc).__name__)
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Chroma vector store directory inaccessible",
        )


def check_embedding_model(settings: Settings) -> DependencyDetail:
    """
    Check if the embedding package is installed.
    Does not download weights on health check.
    """
    spec = importlib.util.find_spec("sentence_transformers")
    if spec is not None:
        return DependencyDetail(
            status=DependencyStatus.ready,
            message=f"Library installed ({settings.embedding_model})",
        )
    return DependencyDetail(
        status=DependencyStatus.degraded,
        message="sentence-transformers package not installed in environment",
    )


async def check_ollama(settings: Settings) -> DependencyDetail:
    """Check if local Ollama daemon is reachable and if the configured model is installed."""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                # Check for exact or base model match (e.g., "gemma3:1b" vs "gemma3:1b-instruct")
                target_model = settings.ollama_model
                model_found = any(
                    target_model == m
                    or m.startswith(f"{target_model}:")
                    or target_model.startswith(f"{m}:")
                    for m in models
                    if m
                )
                if model_found:
                    return DependencyDetail(status=DependencyStatus.ready)
                return DependencyDetail(
                    status=DependencyStatus.degraded,
                    message=f"Model '{target_model}' not found in local Ollama models",
                )
            return DependencyDetail(
                status=DependencyStatus.unavailable,
                message=f"Ollama returned unexpected status {resp.status_code}",
            )
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
        logger.debug("Ollama connectivity check failed: %s", type(exc).__name__)
        return DependencyDetail(
            status=DependencyStatus.unavailable,
            message="Local Ollama service unreachable",
        )


@router.get("/ready", response_model=ReadyResponse)
async def get_ready(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadyResponse:
    """
    Checks per-dependency status: SQLite, Chroma, sentence-transformers, Ollama.
    Sets HTTP 503 if any critical dependency is unavailable, otherwise 200.
    """
    db_status = check_database(settings)
    chroma_status = check_chroma(settings)
    embedding_status = check_embedding_model(settings)
    ollama_status = await check_ollama(settings)

    dependencies = {
        "database": db_status,
        "chroma": chroma_status,
        "embedding_model": embedding_status,
        "ollama": ollama_status,
    }

    statuses = [dep.status for dep in dependencies.values()]
    if DependencyStatus.unavailable in statuses:
        overall = DependencyStatus.unavailable
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif DependencyStatus.degraded in statuses:
        overall = DependencyStatus.degraded
        response.status_code = status.HTTP_200_OK
    else:
        overall = DependencyStatus.ready
        response.status_code = status.HTTP_200_OK

    return ReadyResponse(overall=overall, dependencies=dependencies)
