"""
Pytest fixtures and configuration for GhostArchive backend tests.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

# Ensure offline operation during tests
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def temp_settings(tmp_path: Path) -> Settings:
    """Fixture providing isolated temporary settings pointing to tmp_path."""
    test_data_dir = tmp_path / "test_data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        data_dir=test_data_dir,
        cors_allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="gemma3:1b",
    )


@pytest.fixture
def client(temp_settings: Settings) -> Generator[TestClient, None, None]:
    """TestClient fixture with dependency override for settings."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: temp_settings

    with TestClient(app) as test_client:
        yield test_client
