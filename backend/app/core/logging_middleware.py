from __future__ import annotations

import json
import logging
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Awaitable, Callable

from fastapi import Request, Response
from pydantic_settings import BaseSettings

from app.core.auth import verify_jwt

logger = logging.getLogger(__name__)


def config_presence_summary(settings: BaseSettings) -> dict[str, bool]:
    return {
        "supabase_set": bool(getattr(settings, "supabase_url", "")),
        "supabase_anon_set": bool(getattr(settings, "supabase_anon_key", "")),
        "supabase_jwt_secret_set": bool(
            getattr(settings, "supabase_jwt_secret", "")
        ),
        "gmail_client_id_set": bool(getattr(settings, "gmail_client_id", "")),
        "gmail_client_secret_set": bool(
            getattr(settings, "gmail_client_secret", "")
        ),
        "gmail_redirect_uri_set": bool(
            getattr(settings, "gmail_redirect_uri", "")
        ),
        "oauth_state_secret_set": bool(
            getattr(settings, "oauth_state_secret", "")
        ),
        "openai_set": bool(getattr(settings, "openai_api_key", "")),
        "frontend_url_set": bool(getattr(settings, "frontend_url", "")),
        "allowed_origins_set": bool(getattr(settings, "allowed_origins", "")),
        "sentry_dsn_set": bool(getattr(settings, "sentry_dsn", "")),
        "git_sha_set": bool(getattr(settings, "git_sha", "")),
    }


async def resolve_log_user_id(headers: Mapping[str, str]) -> str | None:
    authorization = headers.get("authorization")
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        claims = await verify_jwt(token)
    except Exception:
        return None
    return str(claims.user_id)


def build_request_log(
    *,
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    user_id: str | None,
) -> None:
    payload: dict[str, object] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if user_id:
        payload["user_id"] = user_id
    logger.info(json.dumps(payload, separators=(",", ":")))


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if request.url.path == "/health":
        return await call_next(request)

    started = time.perf_counter()
    user_id = await resolve_log_user_id(request.headers)
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    build_request_log(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
        user_id=user_id,
    )
    return response
