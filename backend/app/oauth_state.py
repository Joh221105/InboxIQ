import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.config import get_settings

_STATE_TTL_SEC = 600


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def sign_oauth_state(user_id: str) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "uid": user_id,
        "exp": int(time.time()) + _STATE_TTL_SEC,
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    body_b64 = _b64encode(body)
    sig = hmac.new(
        settings.state_signing_key.encode(),
        body_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{body_b64}.{sig}"


def verify_oauth_state(state: str) -> str:
    settings = get_settings()
    try:
        body_b64, sig = state.rsplit(".", 1)
    except ValueError as e:
        raise ValueError("Malformed state") from e
    expected = hmac.new(
        settings.state_signing_key.encode(),
        body_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise ValueError("Invalid state signature")
    payload = json.loads(_b64decode(body_b64).decode())
    if int(time.time()) > int(payload["exp"]):
        raise ValueError("State expired")
    return str(payload["uid"])
