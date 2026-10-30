"""
FastAPI application entry point for GhostArchive.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import configure_logging, get_settings
from app.core.errors import register_exception_handlers
from app.database.connection import initialize_database


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # Ensure private runtime data directories exist safely
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.files_dir.mkdir(parents=True, exist_ok=True)
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        initialize_database(settings)
        yield

    app = FastAPI(
        title="GhostArchive API",
        version=settings.app_version,
        description="Local-first, evidence-grounded AI archive API",
        lifespan=lifespan,
    )

    # CORS configuration - strictly restricted to configured loopback origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register standardized error envelope handlers
    register_exception_handlers(app)

    # Mount API routes
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
