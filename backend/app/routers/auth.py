from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])


@router.get("/start")
async def gmail_oauth_start() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented — see Issue 1B"},
    )


@router.get("/callback")
async def gmail_oauth_callback() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented — see Issue 1B"},
    )
