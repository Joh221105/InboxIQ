# backend/app/routers/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.core.auth import UserClaims, get_current_user
from app.core.config import settings
from app.db.connected_accounts import upsert_account
from app.services.gmail_oauth import (
    OAuthExchangeFailed,
    StateExpired,
    StateInvalid,
    build_authorize_url,
    exchange_code,
    get_gmail_address,
    verify_state,
)

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])


@router.get("/start")
async def gmail_oauth_start(
    return_to: str = "/settings",
    claims: UserClaims = Depends(get_current_user),
) -> dict[str, str]:
    url = build_authorize_url(claims.user_id, return_to)
    return {"url": url}


@router.get("/callback")
async def gmail_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    frontend = settings.frontend_url.rstrip("/")
    return_to = "/settings"

    def err(reason: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"{frontend}{return_to}?gmail_connected=error&reason={reason}",
            status_code=302,
        )

    if error:
        return err("user_cancelled")

    if not state:
        return err("state_invalid")

    try:
        claims = verify_state(state)
        return_to = claims.return_to
    except StateExpired:
        return err("state_expired")
    except StateInvalid:
        return err("state_invalid")

    if not code:
        return err("exchange_failed")

    try:
        tokens = await exchange_code(code)
    except OAuthExchangeFailed:
        return err("exchange_failed")

    if not tokens.refresh_token:
        return err("no_refresh_token")

    email_address = await get_gmail_address(tokens.access_token)

    await upsert_account(
        user_id=claims.user_id,
        email_address=email_address,
        provider="gmail",
        oauth_token=tokens,
    )

    return RedirectResponse(
        url=f"{frontend}{return_to}?gmail_connected=success",
        status_code=302,
    )
