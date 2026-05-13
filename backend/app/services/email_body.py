from __future__ import annotations

import asyncio
import base64
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any
from uuid import UUID

from bs4 import BeautifulSoup

from app.db.connected_accounts import get_account
from app.services.gmail_sync import get_authed_service

_BODY_CACHE_TTL = timedelta(minutes=5)
_BODY_CACHE_MAX = 100
_body_cache: OrderedDict[tuple[UUID, str], tuple[datetime, str]] = OrderedDict()


def _decode_body_data(data: str) -> str:
    remainder = len(data) % 4
    if remainder:
        data += "=" * (4 - remainder)
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def _extract_html_and_plain(payload: dict[str, Any]) -> tuple[str, str]:
    parts = payload.get("parts") or []
    if parts:
        html_parts: list[str] = []
        plain_parts: list[str] = []
        for part in parts:
            html, plain = _extract_html_and_plain(part)
            if html:
                html_parts.append(html)
            if plain:
                plain_parts.append(plain)
        return "".join(html_parts), "\n".join(plain_parts)

    body_data = payload.get("body", {}).get("data")
    if not body_data:
        return "", ""

    decoded = _decode_body_data(body_data)
    mime_type = payload.get("mimeType")
    if mime_type == "text/html":
        return decoded, ""
    if mime_type == "text/plain":
        return "", decoded
    return "", ""


def sanitize_body_html(body_html: str) -> str:
    soup = BeautifulSoup(body_html, "html.parser")
    for tag in soup.find_all("script"):
        tag.decompose()
    return str(soup)


async def fetch_email_body_html(account_id: UUID, gmail_id: str) -> str:
    cache_key = (account_id, gmail_id)
    now = datetime.now(timezone.utc)
    cached = _body_cache.get(cache_key)
    if cached and now - cached[0] < _BODY_CACHE_TTL:
        _body_cache.move_to_end(cache_key)
        return cached[1]

    account = await get_account(account_id)
    service = await get_authed_service(account)

    def _get() -> dict[str, Any]:
        return (
            service.users()
            .messages()
            .get(userId="me", id=gmail_id, format="full")
            .execute()
        )

    msg = await asyncio.to_thread(_get)
    html, plain = _extract_html_and_plain(msg.get("payload", {}))
    body_html = html or f"<pre>{escape(plain)}</pre>"
    sanitized = sanitize_body_html(body_html)

    _body_cache[cache_key] = (now, sanitized)
    _body_cache.move_to_end(cache_key)
    while len(_body_cache) > _BODY_CACHE_MAX:
        _body_cache.popitem(last=False)
    return sanitized
