from __future__ import annotations

import urllib.parse
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.core.config import settings
from app.main import app
from app.services.gmail_oauth import OAuthExchangeFailed, sign_state

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
    t.expires_at = datetime.now(UTC) + timedelta(hours=1)
    t.scope = "https://www.googleapis.com/auth/gmail.modify"
    return t


def test_callback_success_redirects(anon_client: TestClient) -> None:
    state = sign_state({"user_id": str(_USER_ID), "return_to": "/settings"})
    connected_account = SimpleNamespace(id=uuid4())
    with (
        patch(
            "app.routers.auth.exchange_code", new_callable=AsyncMock, return_value=_mock_tokens()
        ),
        patch(
            "app.routers.auth.get_gmail_address",
            new_callable=AsyncMock,
            return_value="me@gmail.com",
        ),
        patch(
            "app.routers.auth.upsert_account",
            new_callable=AsyncMock,
            return_value=connected_account,
        ),
        patch("app.routers.auth.sync_account", new=MagicMock(return_value="sync-coro")),
        patch("app.routers.auth.spawn") as mock_spawn,
    ):
        resp = anon_client.get(
            f"/auth/gmail/callback?code=good_code&state={state}",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    loc = resp.headers["location"]
    assert "gmail_connected=success" in loc
    assert "/settings" in loc
    mock_spawn.assert_called_once_with("sync-coro", name=f"initial-sync:{connected_account.id}")


def test_callback_expired_state(anon_client: TestClient) -> None:
    expired_state = jwt.encode(
        {
            "user_id": str(uuid4()),
            "return_to": "/settings",
            "nonce": "x",
            "exp": (datetime.now(UTC) - timedelta(minutes=1)).timestamp(),
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
            "exp": (datetime.now(UTC) + timedelta(minutes=10)).timestamp(),
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


@pytest.mark.parametrize(
    "target", ["https://evil.example", "//evil.example", "/\\evil.example", "settings"]
)
def test_start_rejects_non_relative_return_to(authed_client: TestClient, target: str) -> None:
    resp = authed_client.get("/auth/gmail/start", params={"return_to": target})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "invalid_return_to"


def _callback(anon_client: TestClient, return_to: str, *, demo_mode: bool = False):
    state = sign_state({"user_id": str(_USER_ID), "return_to": return_to})
    account = SimpleNamespace(id=uuid4())
    with (
        patch.object(settings, "demo_mode", demo_mode),
        patch(
            "app.routers.auth.exchange_code", new_callable=AsyncMock, return_value=_mock_tokens()
        ),
        patch(
            "app.routers.auth.get_gmail_address",
            new_callable=AsyncMock,
            return_value="me@gmail.com",
        ),
        patch("app.routers.auth.upsert_account", new_callable=AsyncMock, return_value=account),
        patch("app.routers.auth.sync_account", new=MagicMock(return_value="sync-coro")),
        patch("app.routers.auth.seed_demo_emails", new=MagicMock(return_value="seed-coro")),
        patch("app.routers.auth.spawn") as spawn,
    ):
        resp = anon_client.get(f"/auth/gmail/callback?code=c&state={state}", follow_redirects=False)
    return resp, spawn, account


def test_callback_ignores_unsafe_return_to_in_state(anon_client: TestClient) -> None:
    resp, _, _ = _callback(anon_client, "//evil.example")
    assert resp.status_code == 302
    assert resp.headers["location"].startswith("http://localhost:3000/settings?")


def test_callback_schedules_only_sync_when_demo_mode_off(anon_client: TestClient) -> None:
    _, spawn, account = _callback(anon_client, "/settings", demo_mode=False)
    assert [c.kwargs["name"] for c in spawn.call_args_list] == [f"initial-sync:{account.id}"]


def test_callback_also_seeds_demo_emails_when_demo_mode_on(anon_client: TestClient) -> None:
    _, spawn, account = _callback(anon_client, "/settings", demo_mode=True)
    assert [c.kwargs["name"] for c in spawn.call_args_list] == [
        f"initial-sync:{account.id}",
        f"demo-seed:{account.id}",
    ]


def test_callback_profile_failure_redirects_with_error(anon_client: TestClient) -> None:
    state = sign_state({"user_id": str(_USER_ID), "return_to": "/settings"})
    with (
        patch(
            "app.routers.auth.exchange_code", new_callable=AsyncMock, return_value=_mock_tokens()
        ),
        patch(
            "app.routers.auth.get_gmail_address",
            new_callable=AsyncMock,
            side_effect=OAuthExchangeFailed("profile 500"),
        ),
    ):
        resp = anon_client.get(f"/auth/gmail/callback?code=c&state={state}", follow_redirects=False)
    assert resp.status_code == 302
    assert "reason=exchange_failed" in resp.headers["location"]
