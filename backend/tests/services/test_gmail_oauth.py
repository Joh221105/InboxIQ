# backend/tests/services/test_gmail_oauth.py
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import jwt
import pytest
import respx

from app.models.connected_account import OAuthTokens
from app.services.gmail_oauth import (
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
