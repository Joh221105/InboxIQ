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
    GOOGLE_TOKEN_URL,
    OAuthExchangeFailed,
    StateExpired,
    StateInvalid,
    _refresh_locks,
    build_authorize_url,
    exchange_code,
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
