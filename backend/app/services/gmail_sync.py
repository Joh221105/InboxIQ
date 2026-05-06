# backend/app/services/gmail_sync.py
from __future__ import annotations

import asyncio
import base64
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
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
from app.services.gmail_oauth import RefreshFailed, refresh_tokens

logger = logging.getLogger(__name__)

INITIAL_SYNC_LIMIT = 50
BODY_PREVIEW_MAX_CHARS = 2000
PER_ACCOUNT_CONCURRENCY = 5


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
