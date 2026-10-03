"""Domain errors and the HTTP error envelope.

Services and the data layer raise these exceptions instead of HTTP errors.
`register_error_handlers` maps them, and any `HTTPException`, to responses
shaped as ``{"detail": {"code": ..., "message": ...}}``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    status_code: ClassVar[int] = 500
    default_code: ClassVar[str] = "internal_error"
    default_message: ClassVar[str] = "Something went wrong."

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        super().__init__(self.message)

    def to_detail(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message}


class BadRequestError(AppError):
    status_code = 400
    default_code = "bad_request"
    default_message = "The request is invalid."


class NotFoundError(AppError):
    status_code = 404
    default_code = "not_found"
    default_message = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    default_code = "conflict"
    default_message = "The request conflicts with the current state."


class RateLimitedError(AppError):
    status_code = 429
    default_code = "rate_limited"
    default_message = "Too many requests. Try again shortly."

    def __init__(self, retry_after_seconds: int, message: str | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds

    def to_detail(self) -> dict[str, Any]:
        return {**super().to_detail(), "retry_after_seconds": self.retry_after_seconds}


def _envelope(
    status_code: int, detail: dict[str, Any], headers: Mapping[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail}, headers=headers)


async def _handle_app_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):  # pragma: no cover - registered for AppError only
        raise exc
    headers = (
        {"Retry-After": str(exc.retry_after_seconds)} if isinstance(exc, RateLimitedError) else None
    )
    return _envelope(exc.status_code, exc.to_detail(), headers)


async def _handle_http_exception(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):  # pragma: no cover
        raise exc
    detail = (
        exc.detail
        if isinstance(exc.detail, dict)
        else {"code": f"http_{exc.status_code}", "message": str(exc.detail)}
    )
    return _envelope(exc.status_code, detail, exc.headers)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
