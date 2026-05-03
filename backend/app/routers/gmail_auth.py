import json
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.auth_jwt import current_user_id
from app.config import get_settings
from app.gmail_oauth import authorization_url, exchange_code, fetch_gmail_profile_email
from app.oauth_state import sign_oauth_state, verify_oauth_state
from app.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])


@router.post("/start")
async def gmail_oauth_start(user_id: str = Depends(current_user_id)):
    state = sign_oauth_state(user_id)
    url = authorization_url(state)
    return {"authorization_url": url}


@router.get("/callback")
async def gmail_oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    settings = get_settings()
    base = settings.frontend_url.rstrip("/")

    if error:
        return RedirectResponse(f"{base}/?gmail_error={quote(error)}")
    if not code or not state:
        return RedirectResponse(f"{base}/?gmail_error=missing_params")

    try:
        uid = verify_oauth_state(state)
    except ValueError:
        return RedirectResponse(f"{base}/?gmail_error=invalid_state")

    try:
        tokens = exchange_code(code)
    except Exception as e:
        logger.warning("Gmail OAuth token exchange failed: %s", e, exc_info=True)
        return RedirectResponse(f"{base}/?gmail_error=token_exchange_failed")

    if not tokens.get("access_token"):
        return RedirectResponse(f"{base}/?gmail_error=no_access_token")

    try:
        email_address = fetch_gmail_profile_email(tokens["access_token"])
    except Exception:
        return RedirectResponse(f"{base}/?gmail_error=profile_failed")

    if not email_address:
        return RedirectResponse(f"{base}/?gmail_error=no_email")

    if not tokens.get("refresh_token"):
        prev = (
            get_supabase()
            .table("connected_accounts")
            .select("oauth_token")
            .eq("user_id", uid)
            .eq("email_address", email_address)
            .eq("provider", "gmail")
            .limit(1)
            .execute()
        )
        rows = prev.data or []
        if rows:
            old = rows[0].get("oauth_token") or {}
            if isinstance(old, str):
                old = json.loads(old)
            if old.get("refresh_token"):
                tokens["refresh_token"] = old["refresh_token"]

    row = {
        "user_id": uid,
        "email_address": email_address,
        "provider": "gmail",
        "oauth_token": tokens,
        "color": "#4285F4",
    }
    try:
        get_supabase().table("connected_accounts").upsert(
            row,
            on_conflict="user_id,email_address,provider",
        ).execute()
    except Exception:
        return RedirectResponse(f"{base}/?gmail_error=database_save_failed")

    return RedirectResponse(f"{base}/?gmail=connected")
