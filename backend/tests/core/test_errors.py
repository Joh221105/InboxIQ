from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    RateLimitedError,
    register_error_handlers,
)


def _client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError("Email not found.")

    @app.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("Already tagged.", code="duplicate_contact")

    @app.get("/bad")
    async def bad() -> None:
        raise BadRequestError()

    @app.get("/limited")
    async def limited() -> None:
        raise RateLimitedError(42)

    @app.get("/http-string")
    async def http_string() -> None:
        raise HTTPException(status_code=403, detail="Forbidden here")

    @app.get("/http-dict")
    async def http_dict() -> None:
        raise HTTPException(status_code=401, detail={"code": "auth_invalid", "message": "Bad"})

    return TestClient(app)


def test_not_found_uses_envelope() -> None:
    resp = _client().get("/not-found")
    assert resp.status_code == 404
    assert resp.json() == {"detail": {"code": "not_found", "message": "Email not found."}}


def test_custom_code_overrides_default() -> None:
    resp = _client().get("/conflict")
    assert resp.status_code == 409
    assert resp.json()["detail"] == {"code": "duplicate_contact", "message": "Already tagged."}


def test_default_message_is_used_when_none_given() -> None:
    resp = _client().get("/bad")
    assert resp.status_code == 400
    assert resp.json()["detail"] == {"code": "bad_request", "message": "The request is invalid."}


def test_rate_limited_sets_retry_after() -> None:
    resp = _client().get("/limited")
    assert resp.status_code == 429
    assert resp.headers["retry-after"] == "42"
    assert resp.json()["detail"]["code"] == "rate_limited"
    assert resp.json()["detail"]["retry_after_seconds"] == 42


def test_string_http_exception_is_wrapped() -> None:
    resp = _client().get("/http-string")
    assert resp.status_code == 403
    assert resp.json() == {"detail": {"code": "http_403", "message": "Forbidden here"}}


def test_dict_http_exception_passes_through() -> None:
    resp = _client().get("/http-dict")
    assert resp.json() == {"detail": {"code": "auth_invalid", "message": "Bad"}}


def test_unknown_route_uses_envelope() -> None:
    resp = _client().get("/missing")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "http_404"
