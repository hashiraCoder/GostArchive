"""
GhostArchive application settings.

All configuration comes from environment variables or a .env file.
Never hardcode environment-specific values in business logic.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GHOSTARCHIVE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ──────────────────────────────────────────────────────────────
    host: str = "127.0.0.1"
    port: int = 8000
    app_version: str = "0.1.0"

    # ── Data directory (runtime; must be gitignored) ─────────────────────────
    data_dir: Path = Path("backend/data")

    # ── Upload limits ────────────────────────────────────────────────────────
    upload_max_bytes: int = 5_242_880  # 5 MiB
    extracted_text_max_chars: int = 500_000

    # ── Ollama (local generation) ────────────────────────────────────────────
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma3:1b"
    ollama_timeout_seconds: int = 60

    # ── Embedding model ──────────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Retrieval ────────────────────────────────────────────────────────────
    retrieval_top_k: int = 5
    retrieval_top_k_max: int = 8
    retrieval_min_similarity: float = 0.30
    retrieval_lexical_boost: bool = True

    # ── CORS — loopback Vite origins only ───────────────────────────────────
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("retrieval_top_k")
    @classmethod
    def clamp_top_k(cls, v: int) -> int:
        return max(1, min(v, 8))

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        level = v.upper()
        if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid log level: {v}")
        return level

    # ── Derived paths (computed; not stored in DB) ───────────────────────────
    @property
    def db_path(self) -> Path:
        return self.data_dir / "ghostarchive.db"

    @property
    def chroma_path(self) -> Path:
        return self.data_dir / "chroma_store"

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "files"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    return Settings()


def configure_logging(settings: Settings) -> None:
    """Apply log level from settings. Call once at startup."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
