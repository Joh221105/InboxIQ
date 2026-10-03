from __future__ import annotations

import json
import logging

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.logging_middleware import build_request_log, request_logging_middleware


def test_presence_summary_reports_only_booleans() -> None:
    summary = settings.presence_summary()

    assert summary["supabase_url_set"] is True
    assert summary["openrouter_api_key_set"] is True
    assert "demo_mode_set" not in summary
    assert all(isinstance(value, bool) for value in summary.values())


def test_presence_summary_omits_service_role_key_status() -> None:
    assert "supabase_service_role_key_set" not in settings.presence_summary()


def test_request_log_includes_user_id_from_request_state(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = FastAPI()
    app.middleware("http")(request_logging_middleware)

    @app.get("/whoami")
    async def whoami(request: Request) -> dict[str, str]:
        request.state.user_id = "user-123"
        return {"ok": "yes"}

    with caplog.at_level(logging.INFO, logger="app.core.logging_middleware"):
        TestClient(app).get("/whoami")

    assert '"user_id":"user-123"' in caplog.text


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
