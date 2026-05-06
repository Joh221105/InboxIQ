# backend/tests/services/test_gmail_oauth.py
from __future__ import annotations

import asyncio
import urllib.parse
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import jwt
import pytest
import respx

from app.models.connected_account import OAuthTokens
from app.services.gmail_oauth import (
    GMAIL_PROFILE_URL,
    GOOGLE_TOKEN_URL,
    OAuthExchangeFailed,
    StateExpired,
    StateInvalid,
    _refresh_locks,
    build_authorize_url,
    exchange_code,
    get_gmail_address,
    refresh_tokens,
    sign_state,
    verify_state,
)


# --- State JWT ---

def test_sign_verify_state_roundtrip() -> None:
    user_id = uuid4()
    token = sign_state({"user_id": str(user_id), "return_to": "/settings"})
    claims = verify_state(token)
    assert claims.user_id == user_id
    assert claims.return_to == "/settings"


def test_verify_state_expired() -> None:
    payload = {
        "user_id": str(uuid4()),
        "return_to": "/settings",
        "nonce": "abc",
        "exp": (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp(),
    }
    token = jwt.encode(payload, "test-oauth-state-secret-at-least-32-chars!", algorithm="HS256")
    with pytest.raises(StateExpired):
        verify_state(token)


def test_verify_state_bad_signature() -> None:
    payload = {
        "user_id": str(uuid4()),
        "return_to": "/settings",
        "nonce": "abc",
        "exp": (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp(),
    }
    token = jwt.encode(payload, "wrong-secret-here-at-least-32-chars!!", algorithm="HS256")
    with pytest.raises(StateInvalid):
        verify_state(token)


# --- build_authorize_url ---


def test_build_authorize_url_contains_required_params() -> None:
    user_id = uuid4()
    url = build_authorize_url(user_id, "/settings")
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert "accounts.google.com" in parsed.netloc
    assert params["client_id"][0] == "test-gmail-client-id.apps.googleusercontent.com"
    assert params["redirect_uri"][0] == "http://localhost:8000/auth/gmail/callback"
    assert params["response_type"][0] == "code"
    assert "https://www.googleapis.com/auth/gmail.readonly" in params["scope"][0]
    assert params["access_type"][0] == "offline"
    assert params["prompt"][0] == "consent"
    assert params["include_granted_scopes"][0] == "true"
    assert "state" in params


# --- exchange_code ---

@pytest.mark.asyncio
async def test_exchange_code_success() -> None:
    with respx.mock:
        respx.post(GOOGLE_TOKEN_URL).mock(
            return_value=httpx.Response(200, json={
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/gmail.readonly",
                "token_type": "Bearer",
            })
        )
        tokens = await exchange_code("auth_code_123")

    assert tokens.access_token == "test_access"
    assert tokens.refresh_token == "test_refresh"
    assert tokens.scope == "https://www.googleapis.com/auth/gmail.readonly"
    assert tokens.expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_exchange_code_google_400_raises() -> None:
    with respx.mock:
        respx.post(GOOGLE_TOKEN_URL).mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        with pytest.raises(OAuthExchangeFailed):
            await exchange_code("bad_code")


# --- get_gmail_address ---


@pytest.mark.asyncio
async def test_get_gmail_address_success() -> None:
    with respx.mock:
        respx.get(GMAIL_PROFILE_URL).mock(
            return_value=httpx.Response(200, json={
                "emailAddress": "user@gmail.com",
                "messagesTotal": 12345,
            })
        )
        address = await get_gmail_address("test_access_token")
    assert address == "user@gmail.com"


# --- refresh_tokens race ---

@pytest.mark.asyncio
async def test_refresh_tokens_race_only_one_google_call() -> None:
    from uuid import UUID
    account_id = uuid4()
    _refresh_locks.pop(account_id, None)  # clean slate

    expired = OAuthTokens(
        access_token="old_access",
        refresh_token="old_refresh",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        scope="https://www.googleapis.com/auth/gmail.readonly",
    )
    fresh = OAuthTokens(
        access_token="new_access",
        refresh_token="old_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="https://www.googleapis.com/auth/gmail.readonly",
    )

    db_call_n = 0

    async def fake_get_account(aid: UUID):  # type: ignore[return]
        nonlocal db_call_n
        db_call_n += 1
        acct = MagicMock()
        # First call (inside lock for coro 1): expired.
        # Second call (inside lock for coro 2): fresh — already refreshed.
        acct.oauth_token = expired if db_call_n == 1 else fresh
        return acct

    google_calls = 0

    with (
        patch("app.services.gmail_oauth.get_account", side_effect=fake_get_account),
        patch("app.services.gmail_oauth.update_oauth_token", new_callable=AsyncMock),
    ):
        with respx.mock:
            def count_google(request: httpx.Request) -> httpx.Response:
                nonlocal google_calls
                google_calls += 1
                return httpx.Response(200, json={
                    "access_token": "new_access",
                    "expires_in": 3600,
                    "scope": "https://www.googleapis.com/auth/gmail.readonly",
                    "token_type": "Bearer",
                })

            respx.post(GOOGLE_TOKEN_URL).mock(side_effect=count_google)

            await asyncio.gather(
                refresh_tokens(account_id, "old_refresh"),
                refresh_tokens(account_id, "old_refresh"),
            )

    assert google_calls == 1, f"Expected 1 Google call, got {google_calls}"
