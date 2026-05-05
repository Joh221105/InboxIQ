from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, users

logger = logging.getLogger(__name__)

_REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "GMAIL_CLIENT_ID",
    "GMAIL_CLIENT_SECRET",
    "GMAIL_REDIRECT_URI",
    "OAUTH_STATE_SECRET",
    "OPENAI_API_KEY",
    "FRONTEND_URL",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    for var in _REQUIRED_ENV_VARS:
        logger.info("env %s present=%s", var, bool(os.getenv(var)))
    yield


app = FastAPI(title="InboxIQ API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)


async def _probe_supabase() -> str:
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/health"
            )
            return "ok" if resp.status_code == 200 else "down"
    except Exception:
        return "down"


async def _probe_openai() -> str:
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            )
            return "ok" if resp.status_code == 200 else "down"
    except Exception:
        return "down"


@app.get("/health")
async def health() -> dict:
    supabase_status, openai_status = await asyncio.gather(
        _probe_supabase(), _probe_openai()
    )
    return {
        "status": "ok",
        "version": settings.git_sha,
        "deps": {"supabase": supabase_status, "openai": openai_status},
    }
