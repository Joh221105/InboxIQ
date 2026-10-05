from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.core.auth import UserClaims, get_current_user
from app.core.background import spawn
from app.core.config import settings
from app.core.errors import BadRequestError
from app.db.connected_accounts import upsert_account
from app.demo.seed import seed_demo_emails
from app.services.gmail_oauth import (
    OAuthExchangeFailed,
    StateExpired,
    StateInvalid,
    build_authorize_url,
    exchange_code,
    get_gmail_address,
    is_safe_return_path,
    verify_state,
)
from app.services.gmail_sync import sync_account

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])
logger = logging.getLogger(__name__)


@router.get("/start")
async def gmail_oauth_start(
    return_to: str = "/settings",
    claims: UserClaims = Depends(get_current_user),
) -> dict[str, str]:
    if not is_safe_return_path(return_to):
        raise BadRequestError("return_to must be a path on this site.", code="invalid_return_to")
    return {"url": build_authorize_url(claims.user_id, return_to)}


@router.get("/callback")
async def gmail_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    frontend = settings.frontend_url.rstrip("/")
    return_to = "/settings"

    def redirect(query: str) -> RedirectResponse:
        return RedirectResponse(url=f"{frontend}{return_to}?{query}", status_code=302)

    def fail(reason: str) -> RedirectResponse:
        return redirect(f"gmail_connected=error&reason={reason}")

    if error:
        return fail("user_cancelled")
    if not state:
        return fail("state_invalid")
    try:
        claims = verify_state(state)
    except StateExpired:
        return fail("state_expired")
    except StateInvalid:
        return fail("state_invalid")
    # The state is signed, but re-check in case a token predates the /start validation.
    if is_safe_return_path(claims.return_to):
        return_to = claims.return_to
    if not code:
        return fail("exchange_failed")

    try:
        tokens = await exchange_code(code)
        if not tokens.refresh_token:
            return fail("no_refresh_token")
        email_address = await get_gmail_address(tokens.access_token)
    except OAuthExchangeFailed as exc:
        logger.warning("gmail oauth exchange failed: %s", exc)
        return fail("exchange_failed")

    account = await upsert_account(
        user_id=claims.user_id,
        email_address=email_address,
        provider="gmail",
        oauth_token=tokens,
    )
    spawn(sync_account(account.id), name=f"initial-sync:{account.id}")
    if settings.demo_mode:
        spawn(seed_demo_emails(claims.user_id, account.id), name=f"demo-seed:{account.id}")
    return redirect("gmail_connected=success")
