from __future__ import annotations

import time
from typing import Any
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

# Module-level JWKS cache: {"keys": [...], "expires_at": float}
_jwks_cache: dict[str, Any] = {}

_bearer = HTTPBearer(auto_error=False)


class UserClaims(BaseModel):
    user_id: UUID
    email: str


def _invalid(msg: str = "Invalid token") -> HTTPException:
    return HTTPException(status_code=401, detail={"code": "auth_invalid", "message": msg})


def _expired() -> HTTPException:
    return HTTPException(
        status_code=401, detail={"code": "auth_expired", "message": "Token expired"}
    )


async def _fetch_jwks() -> list[dict[str, Any]]:
    now = time.monotonic()
    if _jwks_cache.get("expires_at", 0.0) > now:
        return _jwks_cache["keys"]
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    _jwks_cache["keys"] = data["keys"]
    _jwks_cache["expires_at"] = now + 300.0
    return data["keys"]


async def verify_jwt(token: str) -> UserClaims:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise _invalid() from None

    alg = header.get("alg", "HS256")

    try:
        if alg in ("ES256", "RS256"):
            keys = await _fetch_jwks()
            kid = header.get("kid")
            from jwt import PyJWKSet

            jwk_set = PyJWKSet.from_dict({"keys": keys})
            signing_key = None
            for k in jwk_set.keys:
                if kid is None or k.key_id == kid:
                    signing_key = k.key
                    break
            if signing_key is None:
                raise _invalid("No matching JWKS key")
            payload = jwt.decode(token, signing_key, algorithms=[alg], audience="authenticated")
        else:
            if not settings.supabase_jwt_secret:
                raise _invalid("HS256 not configured")
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except jwt.ExpiredSignatureError:
        raise _expired() from None
    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise _invalid() from None

    sub = payload.get("sub")
    if not sub:
        raise _invalid("Missing sub claim")

    try:
        return UserClaims(user_id=UUID(str(sub)), email=payload.get("email", ""))
    except (ValueError, TypeError):
        raise _invalid("Invalid sub UUID") from None


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserClaims:
    if not creds or creds.scheme.lower() != "bearer":
        raise _invalid("Missing bearer token")
    return await verify_jwt(creds.credentials)
