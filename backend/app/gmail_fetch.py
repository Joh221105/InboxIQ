from datetime import datetime, timezone
from typing import Any

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.auth_jwt import GOOGLE_SCOPES
from app.config import get_settings
from app.supabase_client import get_supabase


def _creds_from_token_blob(blob: dict[str, Any]) -> Credentials:
    scopes = blob.get("scopes") or list(GOOGLE_SCOPES)
    return Credentials(
        token=blob.get("access_token"),
        refresh_token=blob.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_settings().gmail_client_id,
        client_secret=get_settings().gmail_client_secret,
        scopes=scopes,
    )


def _persist_token_update(account_id: str, blob: dict[str, Any], creds: Credentials) -> None:
    blob = dict(blob)
    blob["access_token"] = creds.token
    if creds.refresh_token:
        blob["refresh_token"] = creds.refresh_token
    if creds.expiry:
        blob["expires_at"] = int(creds.expiry.timestamp())
    get_supabase().table("connected_accounts").update({"oauth_token": blob}).eq("id", account_id).execute()


def get_valid_credentials_for_user(user_id: str) -> tuple[str, dict[str, Any], Credentials]:
    sb = get_supabase()
    res = (
        sb.table("connected_accounts")
        .select("id, oauth_token")
        .eq("user_id", user_id)
        .eq("provider", "gmail")
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise ValueError("No Gmail account connected")
    row = rows[0]
    account_id = row["id"]
    blob = row["oauth_token"]
    if isinstance(blob, str):
        import json

        blob = json.loads(blob)
    creds = _creds_from_token_blob(blob)
    if creds.expired and creds.refresh_token:
        creds.refresh(google.auth.transport.requests.Request())
        _persist_token_update(account_id, blob, creds)
    elif creds.expired:
        raise ValueError("Gmail token expired; reconnect your account")
    return account_id, blob, creds


def list_message_previews(user_id: str, max_results: int = 15) -> list[dict[str, Any]]:
    account_id, _, creds = get_valid_credentials_for_user(user_id)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    lst = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results)
        .execute()
    )
    messages = lst.get("messages") or []
    out: list[dict[str, Any]] = []
    for m in messages:
        mid = m["id"]
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=mid, format="metadata", metadataHeaders=["Subject", "From", "Date"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        out.append(
            {
                "id": mid,
                "thread_id": detail.get("threadId"),
                "snippet": detail.get("snippet"),
                "subject": headers.get("Subject"),
                "from": headers.get("From"),
                "date": headers.get("Date"),
            }
        )
    now = datetime.now(timezone.utc).isoformat()
    get_supabase().table("connected_accounts").update({"last_synced": now}).eq("id", account_id).execute()
    return out
