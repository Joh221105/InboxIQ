from __future__ import annotations

import json
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from fastapi import Request, Response

logger = logging.getLogger(__name__)


def build_request_log(
    *,
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    user_id: str | None,
) -> None:
    payload: dict[str, object] = {
        "ts": datetime.now(UTC).isoformat(),
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
    response = await call_next(request)
    # Set by get_current_user, so the JWT is verified once per request.
    user_id = getattr(request.state, "user_id", None)
    build_request_log(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=(time.perf_counter() - started) * 1000,
        user_id=str(user_id) if user_id else None,
    )
    return response
