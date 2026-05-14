from __future__ import annotations

import json
import logging
from uuid import UUID

import pytest
from starlette.datastructures import Headers

from app.core.auth import UserClaims
from app.core.logging_middleware import (
    build_request_log,
    config_presence_summary,
    resolve_log_user_id,
)
from app.core.config import settings


def test_config_presence_summary_uses_booleans_only() -> None:
    summary = config_presence_summary(settings)

    assert summary["supabase_set"] is True
    assert summary["openai_set"] is True
    assert all(isinstance(value, bool) for value in summary.values())


@pytest.mark.asyncio
async def test_resolve_log_user_id_returns_valid_bearer_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_verify_jwt(token: str) -> UserClaims:
        assert token == "valid"
        return UserClaims(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            email="demo@example.com",
        )

    monkeypatch.setattr("app.core.logging_middleware.verify_jwt", fake_verify_jwt)

    user_id = await resolve_log_user_id(Headers({"authorization": "Bearer valid"}))

    assert user_id == "12345678-1234-5678-1234-567812345678"


@pytest.mark.asyncio
async def test_resolve_log_user_id_omits_invalid_or_missing_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_verify_jwt(token: str) -> UserClaims:
        raise AssertionError("verify_jwt should not run without a bearer token")

    monkeypatch.setattr("app.core.logging_middleware.verify_jwt", fake_verify_jwt)

    assert await resolve_log_user_id(Headers({})) is None
    assert await resolve_log_user_id(Headers({"authorization": "Basic abc"})) is None


def test_build_request_log_is_json_serializable(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.core.logging_middleware")

    build_request_log(
        method="GET",
        path="/emails",
        status=401,
        duration_ms=12.5,
        user_id=None,
    )

    record = caplog.records[0]
    payload = json.loads(record.getMessage())
    assert payload["method"] == "GET"
    assert payload["path"] == "/emails"
    assert payload["status"] == 401
    assert payload["duration_ms"] == 12.5
    assert "user_id" not in payload
