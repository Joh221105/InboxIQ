from __future__ import annotations

import json
import time
from uuid import uuid4

import httpx
import jwt
import pytest
import respx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from jwt.algorithms import ECAlgorithm

from app.core import auth as auth_module
from app.core.auth import UserClaims, verify_jwt

_SECRET = "super-secret-test-jwt-secret-at-least-32-chars!"
_USER_ID = str(uuid4())
_EMAIL = "test@example.com"
_SUPABASE_URL = "https://testproject.supabase.co"


def _hs256_token(
    user_id: str = _USER_ID,
    email: str = _EMAIL,
    expired: bool = False,
    omit_sub: bool = False,
) -> str:
    now = int(time.time())
    payload: dict = {
        "aud": "authenticated",
        "iat": now - 10,
        "exp": (now - 60) if expired else (now + 3600),
        "email": email,
    }
    if not omit_sub:
        payload["sub"] = user_id
    return jwt.encode(payload, _SECRET, algorithm="HS256")


async def test_hs256_happy_path() -> None:
    token = _hs256_token()
    claims = await verify_jwt(token)
    assert isinstance(claims, UserClaims)
    assert str(claims.user_id) == _USER_ID
    assert claims.email == _EMAIL


async def test_hs256_expired_raises_auth_expired() -> None:
    token = _hs256_token(expired=True)
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "auth_expired"


async def test_hs256_mangled_raises_auth_invalid() -> None:
    with pytest.raises(HTTPException) as exc:
        await verify_jwt("this.is.garbage")
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "auth_invalid"


async def test_hs256_missing_sub_raises_auth_invalid() -> None:
    token = _hs256_token(omit_sub=True)
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "auth_invalid"


async def test_es256_with_mocked_jwks() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    kid = "test-ec-key-id"
    now = int(time.time())
    payload = {
        "aud": "authenticated",
        "sub": _USER_ID,
        "email": _EMAIL,
        "iat": now - 10,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})

    pub_jwk = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    pub_jwk.update({"kid": kid, "alg": "ES256", "use": "sig"})
    jwks_payload = {"keys": [pub_jwk]}

    # Clear JWKS cache so the mock is actually called
    auth_module._jwks_cache.clear()

    jwks_url = f"{_SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    with respx.mock:
        respx.get(jwks_url).mock(return_value=httpx.Response(200, json=jwks_payload))
        claims = await verify_jwt(token)

    assert str(claims.user_id) == _USER_ID
    assert claims.email == _EMAIL
