"""
Health and readiness response schemas.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DependencyStatus(StrEnum):
    ready = "ready"
    degraded = "degraded"
    unavailable = "unavailable"


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    app_version: str


class DependencyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DependencyStatus
    message: str | None = None


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall: DependencyStatus
    dependencies: dict[str, DependencyDetail]
