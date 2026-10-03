from __future__ import annotations

import asyncio
import base64
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast
from uuid import UUID

import httplib2
import tenacity
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.db.connected_accounts import (
    get_account,
    mark_disconnected,
    update_last_synced,
)
from app.db.emails import upsert_email
from app.models.connected_account import ConnectedAccount
from app.models.email import ParsedEmail, SyncResult
from app.services.contact_tags import find_contact_tag
from app.services.gmail_oauth import RefreshFailed, refresh_tokens

logger = logging.getLogger(__name__)

INITIAL_SYNC_LIMIT = 50
BODY_PREVIEW_MAX_CHARS = 2000
PER_ACCOUNT_CONCURRENCY = 5


def _is_retryable_http_error(exc: BaseException) -> bool:
    return isinstance(exc, HttpError) and exc.resp.status in (429, 500, 502, 503, 504)


def _extract(payload: dict) -> tuple[str, str]:
    """Recursively extract (plain_text, html_text) from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts") or []

    if parts:
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in parts:
            p, h = _extract(part)
            if p:
                plain_parts.append(p)
            if h:
                html_parts.append(h)
        return " ".join(plain_parts), " ".join(html_parts)

    body_data = payload.get("body", {}).get("data", "")
    if not body_data:
        return "", ""

    # Gmail uses base64url without padding — add it back
    remainder = len(body_data) % 4
    if remainder:
        body_data += "=" * (4 - remainder)
    try:
        decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
    except Exception:
        return "", ""

    if mime_type == "text/plain":
        return decoded.strip(), ""
    if mime_type == "text/html":
        soup = BeautifulSoup(decoded, "html.parser")
        text = " ".join(soup.get_text(" ").split())
        return "", text
    return "", ""


def parse_payload(payload: dict) -> str:
    plain, html = _extract(payload)
    text = plain or html
    return text[:BODY_PREVIEW_MAX_CHARS]


async def get_authed_service(account: ConnectedAccount) -> Any:
    tokens = account.oauth_token
    if tokens.expires_at < datetime.now(UTC) + timedelta(seconds=60):
        tokens = await refresh_tokens(account.id, tokens.refresh_token)

    creds = Credentials(
        token=tokens.access_token,
        token_uri="https://oauth2.googleapis.com/token",
    )

    def _build():
        authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=30))
        return build("gmail", "v1", http=authed_http, cache_discovery=False)

    return await asyncio.to_thread(_build)


async def archive_gmail_message(account_id: UUID, gmail_id: str) -> None:
    account = await get_account(account_id)
    service = await get_authed_service(account)

    def _archive() -> None:
        (
            service.users()
            .messages()
            .modify(
                userId="me",
                id=gmail_id,
                body={"removeLabelIds": ["INBOX"]},
            )
            .execute()
        )

    await asyncio.to_thread(_archive)


async def list_message_ids(service, after_unix_seconds: int | None) -> list[str]:
    def _list() -> list[str]:
        ids: list[str] = []
        kwargs: dict = {"userId": "me"}
        if after_unix_seconds is None:
            kwargs["maxResults"] = INITIAL_SYNC_LIMIT
        else:
            kwargs["q"] = f"after:{after_unix_seconds}"

        while True:
            resp = service.users().messages().list(**kwargs).execute()
            ids.extend(m["id"] for m in resp.get("messages", []))
            page_token = resp.get("nextPageToken")
            if not page_token or after_unix_seconds is None:
                break
            kwargs["pageToken"] = page_token

        return ids

    async for attempt in tenacity.AsyncRetrying(
        retry=tenacity.retry_if_exception(_is_retryable_http_error),
        wait=tenacity.wait_random_exponential(multiplier=1, max=30),
        stop=tenacity.stop_after_attempt(3),
        reraise=True,
    ):
        with attempt:
            return await asyncio.to_thread(_list)
    raise RuntimeError("unreachable")


_SENDER_RE = re.compile(r"<([^>]+)>")
_DISPLAY_NAME_RE = re.compile(r'^"?([^"<]+?)"?\s*<')


async def fetch_message(service, message_id: str) -> ParsedEmail | None:
    def _get() -> dict | None:
        try:
            return (
                service.users().messages().get(userId="me", id=message_id, format="full").execute()
            )
        except HttpError as exc:
            if exc.resp.status == 404:
                return None
            raise

    async def _fetch_with_retry() -> dict | None:
        async for attempt in tenacity.AsyncRetrying(
            retry=tenacity.retry_if_exception(_is_retryable_http_error),
            wait=tenacity.wait_random_exponential(multiplier=1, max=30),
            stop=tenacity.stop_after_attempt(3),
            reraise=True,
        ):
            with attempt:
                return await asyncio.to_thread(_get)
        return None  # unreachable; tenacity reraises on exhaustion

    msg = await _fetch_with_retry()
    if msg is None:
        return None

    payload = msg.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    subject = headers.get("Subject", "")
    from_header = headers.get("From", "")
    m = _SENDER_RE.search(from_header)
    sender_email = (m.group(1) if m else from_header).lower().strip()
    name_match = _DISPLAY_NAME_RE.match(from_header)
    sender_name = name_match.group(1).strip() if name_match else None
    if not sender_name and "@" in sender_email:
        sender_name = sender_email.split("@", 1)[0]

    internal_date_ms = msg.get("internalDate")
    if internal_date_ms:
        received_at = datetime.fromtimestamp(int(internal_date_ms) / 1000, tz=UTC)
    else:
        received_at = datetime.now(UTC)

    body_preview = parse_payload(payload)

    return ParsedEmail(
        external_id=message_id,
        sender_email=sender_email,
        sender_name=sender_name,
        subject=subject,
        body_preview=body_preview,
        received_at=received_at,
    )


async def sync_account(account_id: UUID) -> SyncResult:
    account = await get_account(account_id)

    if account.disconnected_at is not None:
        return SyncResult(fetched=0, inserted=0, updated=0, errors=0)

    # Capture time before sync so any emails arriving during the job are fetched next run
    sync_started_at = datetime.now(UTC)

    try:
        service = await get_authed_service(account)
    except RefreshFailed as exc:
        if exc.is_invalid_grant:
            await mark_disconnected(account_id, "invalid_grant")
        else:
            logger.warning(
                "Token refresh failed for account %s (non-grant error): %s", account_id, exc
            )
        return SyncResult(fetched=0, inserted=0, updated=0, errors=1)

    after = int(account.last_synced.timestamp()) if account.last_synced else None

    message_ids = await list_message_ids(service, after)
    semaphore = asyncio.Semaphore(PER_ACCOUNT_CONCURRENCY)

    async def process(mid: str) -> tuple[Literal["inserted", "updated", "skipped"], str]:
        async with semaphore:
            parsed = await fetch_message(service, mid)
            if parsed is None:
                return ("skipped", mid)
            contact_tag_id = await find_contact_tag(account.user_id, parsed.sender_email)
            outcome = await upsert_email(
                account_id,
                account.user_id,
                parsed,
                contact_tag_id=contact_tag_id,
            )
            return (outcome, mid)

    results = await asyncio.gather(*[process(m) for m in message_ids], return_exceptions=True)

    inserted = updated = errors = 0
    for r in results:
        if isinstance(r, Exception):
            logger.error("sync_account error for account %s: %s", account_id, r)
            errors += 1
            continue
        outcome = cast(tuple[Literal["inserted", "updated", "skipped"], str], r)
        if outcome[0] == "inserted":
            inserted += 1
        elif outcome[0] == "updated":
            updated += 1

    if errors == 0:
        await update_last_synced(account_id, sync_started_at)

    return SyncResult(
        fetched=len(message_ids),
        inserted=inserted,
        updated=updated,
        errors=errors,
    )
