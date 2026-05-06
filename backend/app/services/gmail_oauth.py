# backend/app/services/gmail_oauth.py
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
import jwt
from pydantic import BaseModel

from app.core.config import settings
from app.models.connected_account import OAuthTokens

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"

_refresh_locks: dict[UUID, asyncio.Lock] = {}


# --- Exceptions ---

class StateInvalid(Exception):
    pass


class StateExpired(Exception):
    pass


class OAuthExchangeFailed(Exception):
    pass


class RefreshFailed(Exception):
    def __init__(self, *, is_invalid_grant: bool) -> None:
        self.is_invalid_grant = is_invalid_grant
        super().__init__("Token refresh failed")


# --- State claim model ---

class StateClaims(BaseModel):
    user_id: UUID
    return_to: str
    nonce: str


# --- State signing ---

def sign_state(claims: dict) -> str:
    payload = {
        **claims,
        "nonce": uuid.uuid4().hex,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.oauth_state_secret, algorithm="HS256")


def verify_state(token: str) -> StateClaims:
    try:
        payload = jwt.decode(
            token,
            settings.oauth_state_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "user_id", "return_to", "nonce"]},
        )
        return StateClaims(**payload)
    except jwt.ExpiredSignatureError:
        raise StateExpired()
    except (jwt.PyJWTError, Exception):
        raise StateInvalid()


def build_authorize_url(user_id: UUID, return_to: str) -> str:
    raise NotImplementedError


async def exchange_code(code: str) -> OAuthTokens:
    raise NotImplementedError


async def get_gmail_address(access_token: str) -> str:
    raise NotImplementedError


async def refresh_tokens(account_id: UUID, refresh_token: str) -> OAuthTokens:
    raise NotImplementedError


async def revoke(refresh_token: str) -> None:
    raise NotImplementedError
