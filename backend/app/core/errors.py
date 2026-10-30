"""
Error models, error codes, and exception handlers for GhostArchive.

Ensures all errors returned by the API adhere to the standard ErrorEnvelope shape:
{
    "error": {
        "code": "MODEL_UNAVAILABLE",
        "message": "The local language model is not available.",
        "retryable": true
    }
}
"""

from __future__ import annotations

import logging
from enum import StrEnum

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ghostarchive.errors")


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    EMBEDDING_UNAVAILABLE = "EMBEDDING_UNAVAILABLE"
    GENERATION_FAILED = "GENERATION_FAILED"
    STORE_ERROR = "STORE_ERROR"
    INVALID_STATE = "INVALID_STATE"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class GhostArchiveException(Exception):
    """Base exception for application-level errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform exception handlers returning ErrorEnvelope."""

    @app.exception_handler(GhostArchiveException)
    async def ghostarchive_exception_handler(
        request: Request, exc: GhostArchiveException
    ) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid request payload or parameters.",
                retryable=False,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=envelope.model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            status.HTTP_404_NOT_FOUND: ErrorCode.NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY: ErrorCode.VALIDATION_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE: ErrorCode.MODEL_UNAVAILABLE,
        }
        code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        message = str(exc.detail) if exc.detail else "An HTTP error occurred."
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=code,
                message=message,
                retryable=(exc.status_code >= 500),
            )
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak traceback or private storage paths to client
        logger.error("Unhandled server exception: %s", type(exc).__name__)
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected internal error occurred.",
                retryable=True,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=envelope.model_dump(),
        )
