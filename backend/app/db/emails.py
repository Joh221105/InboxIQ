# backend/app/db/emails.py
from __future__ import annotations

import asyncio
import base64
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.db.supabase import get_service_client
from app.models.email import Email, EmailFilters, EmailListPage, ParsedEmail


def _cursor_encode(received_at: datetime, email_id: UUID) -> str:
    raw = f"{received_at.isoformat()}|{email_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _cursor_decode(cursor: str) -> tuple[str, str]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    rt, eid = raw.split("|", 1)
    return rt, eid


def _row_to_email(row: dict[str, Any]) -> Email:
    nested = row.pop("connected_accounts", None) or {}
    account_color = nested.get("color") if isinstance(nested, dict) else None
    return Email(**row, account_color=account_color)


async def upsert_email(
    account_id: UUID,
    user_id: UUID,
    parsed: ParsedEmail,
) -> Literal["inserted", "updated"]:
    def _do() -> str:
        result = get_service_client().rpc(
            "upsert_email_record",
            {
                "p_account_id": str(account_id),
                "p_user_id": str(user_id),
                "p_gmail_id": parsed.external_id,
                "p_subject": parsed.subject,
                "p_sender": parsed.sender_email,
                "p_body_text": parsed.body_preview,
                "p_received_at": parsed.received_at.isoformat(),
            },
        ).execute()
        return result.data  # "inserted" or "updated"

    return await asyncio.to_thread(_do)  # type: ignore[return-value]


async def list_emails(filters: EmailFilters) -> EmailListPage:
    limit = min(filters.limit, 100)

    def _fetch() -> list[dict[str, Any]]:
        q = (
            get_service_client()
            .table("emails")
            .select("*, connected_accounts(color)")
            .eq("user_id", str(filters.user_id))
            .eq("is_archived", filters.is_archived)
        )

        if filters.account_id:
            q = q.eq("account_id", str(filters.account_id))

        if filters.triage_category:
            q = q.eq("ai_category", filters.triage_category)

        if filters.since:
            q = q.gte("received_at", filters.since.isoformat())

        if filters.search:
            q = q.ilike("subject", f"%{filters.search}%")

        if filters.cursor:
            rt, eid = _cursor_decode(filters.cursor)
            q = q.or_(f"received_at.lt.{rt},and(received_at.eq.{rt},id.lt.{eid})")

        q = q.order("received_at", desc=True).order("id", desc=True).limit(limit + 1)
        return q.execute().data or []

    rows = await asyncio.to_thread(_fetch)

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_row_to_email(r) for r in page_rows]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        if last.received_at:
            next_cursor = _cursor_encode(last.received_at, last.id)

    return EmailListPage(items=items, next_cursor=next_cursor)


async def get_email(email_id: UUID, user_id: UUID) -> Email | None:
    def _fetch() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("emails")
            .select("*, connected_accounts(color)")
            .eq("id", str(email_id))
            .eq("user_id", str(user_id))
            .maybe_single()
            .execute()
        )
        return result.data

    row = await asyncio.to_thread(_fetch)
    if not row:
        return None
    return _row_to_email(row)
