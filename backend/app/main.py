from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging_middleware import (
    config_presence_summary,
    request_logging_middleware,
)
from app.routers import accounts, auth, contacts, digest, emails, pickup, triage, users
from app.tasks.ai_worker import run_forever as run_ai_worker
from app.tasks.scheduler import make_scheduler

logger = logging.getLogger(__name__)

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))


def _init_sentry() -> None:
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
    except ImportError:
        logger.warning("sentry dsn configured but sentry-sdk is not installed")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.git_sha,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()],
    )


_init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("config loaded", extra=config_presence_summary(settings))
    scheduler = make_scheduler()
    scheduler.start()
    ai_worker_task = asyncio.create_task(run_ai_worker())
    try:
        yield
    finally:
        ai_worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ai_worker_task
        scheduler.shutdown(wait=False)


app = FastAPI(title="InboxIQ API", version="0.1.0", lifespan=lifespan)
register_error_handlers(app)

app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(emails.router)
app.include_router(pickup.router)
app.include_router(triage.router)
app.include_router(digest.router)
app.include_router(contacts.router)


async def _probe_supabase() -> str:
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/health")
            return "ok" if resp.status_code == 200 else "down"
    except httpx.HTTPError:
        return "down"


async def _probe_ai() -> str:
    return "ok" if (settings.openrouter_api_key or settings.anthropic_api_key) else "not_configured"


@app.get("/health")
async def health() -> dict[str, Any]:
    supabase_status, ai_status = await asyncio.gather(_probe_supabase(), _probe_ai())
    return {
        "status": "ok",
        "version": settings.git_sha,
        "deps": {"supabase": supabase_status, "ai": ai_status},
    }
