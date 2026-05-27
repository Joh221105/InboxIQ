# backend/tests/routers/test_auth_oauth.py
from __future__ import annotations

import urllib.parse
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.services.gmail_oauth import sign_state

_USER_ID = uuid4()
_EMAIL = "owner@example.com"


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email=_EMAIL)


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client() -> TestClient:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- GET /auth/gmail/start ---

def test_start_returns_google_url(authed_client: TestClient) -> None:
    resp = authed_client.get("/auth/gmail/start?return_to=/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    parsed = urllib.parse.urlparse(data["url"])
    params = urllib.parse.parse_qs(parsed.query)
    assert "accounts.google.com" in parsed.netloc
    assert params["client_id"][0] == "test-gmail-client-id.apps.googleusercontent.com"
    assert params["response_type"][0] == "code"
    assert params["prompt"][0] == "consent"
    assert params["access_type"][0] == "offline"
    assert "state" in params


def test_start_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.get("/auth/gmail/start?return_to=/settings")
    assert resp.status_code == 401


# --- GET /auth/gmail/callback ---

def _mock_tokens() -> MagicMock:
    t = MagicMock()
    t.access_token = "acc"
    t.refresh_token = "ref"
    t.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    t.scope = "https://www.googleapis.com/auth/gmail.modify"
    return t


def test_callback_success_redirects(anon_client: TestClient) -> None:
    state = sign_state({"user_id": str(_USER_ID), "return_to": "/settings"})
    connected_account = SimpleNamespace(id=uuid4())
    with (
        patch("app.routers.auth.exchange_code", new_callable=AsyncMock, return_value=_mock_tokens()),
        patch("app.routers.auth.get_gmail_address", new_callable=AsyncMock, return_value="me@gmail.com"),
        patch("app.routers.auth.upsert_account", new_callable=AsyncMock, return_value=connected_account),
        patch("app.routers.auth._schedule_initial_sync") as mock_schedule,
    ):
        resp = anon_client.get(
            f"/auth/gmail/callback?code=good_code&state={state}",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    loc = resp.headers["location"]
    assert "gmail_connected=success" in loc
    assert "/settings" in loc
    mock_schedule.assert_called_once_with(connected_account.id)


def test_callback_expired_state(anon_client: TestClient) -> None:
    expired_state = jwt.encode(
        {
            "user_id": str(uuid4()),
            "return_to": "/settings",
            "nonce": "x",
            "exp": (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp(),
        },
        "test-oauth-state-secret-at-least-32-chars!",
        algorithm="HS256",
    )
    resp = anon_client.get(
        f"/auth/gmail/callback?code=x&state={expired_state}",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "reason=state_expired" in resp.headers["location"]


def test_callback_bad_signature_state(anon_client: TestClient) -> None:
    bad_state = jwt.encode(
        {
            "user_id": str(uuid4()),
            "return_to": "/settings",
            "nonce": "x",
            "exp": (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp(),
        },
        "totally-wrong-secret-at-least-32-chars!!",
        algorithm="HS256",
    )
    resp = anon_client.get(
        f"/auth/gmail/callback?code=x&state={bad_state}",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "reason=state_invalid" in resp.headers["location"]


def test_callback_user_cancelled(anon_client: TestClient) -> None:
    resp = anon_client.get(
        "/auth/gmail/callback?error=access_denied&state=irrelevant",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "reason=user_cancelled" in resp.headers["location"]


def test_callback_exchange_failed(anon_client: TestClient) -> None:
    from app.services.gmail_oauth import OAuthExchangeFailed
    state = sign_state({"user_id": str(_USER_ID), "return_to": "/settings"})
    with patch(
        "app.routers.auth.exchange_code",
        new_callable=AsyncMock,
        side_effect=OAuthExchangeFailed("bad code"),
    ):
        resp = anon_client.get(
            f"/auth/gmail/callback?code=bad_code&state={state}",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    assert "reason=exchange_failed" in resp.headers["location"]


def test_callback_no_refresh_token(anon_client: TestClient) -> None:
    state = sign_state({"user_id": str(_USER_ID), "return_to": "/settings"})
    no_refresh = MagicMock()
    no_refresh.access_token = "acc"
    no_refresh.refresh_token = ""  # empty string is falsy
    with (
        patch("app.routers.auth.exchange_code", new_callable=AsyncMock, return_value=no_refresh),
    ):
        resp = anon_client.get(
            f"/auth/gmail/callback?code=good_code&state={state}",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    assert "reason=no_refresh_token" in resp.headers["location"]
