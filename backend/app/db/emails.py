from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from app.db.supabase import get_service_client
from app.models.email import Email, EmailCounts, EmailFilters, EmailListPage, EmailUpdate, ParsedEmail

_COUNTS_CACHE_TTL = timedelta(seconds=30)
_counts_cache: dict[UUID, tuple[datetime, EmailCounts]] = {}


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
    account_email = nested.get("email_address") if isinstance(nested, dict) else None
    if "ai_category" in row and "triage_category" not in row:
        row["triage_category"] = row.get("ai_category")
    if "sender" in row and "sender_email" not in row:
        row["sender_email"] = row.get("sender")
    raw_items = row.get("action_items")
    if raw_items is None:
        row["action_items"] = []
    return Email(**row, account_color=account_color, account_email=account_email)


def _clear_counts_cache(user_id: UUID) -> None:
    _counts_cache.pop(user_id, None)


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
            .select("*, connected_accounts(color,email_address)")
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
            q = q.filter("search_tsv", "plfts(english)", filters.search)

        if filters.cursor:
            rt, eid = _cursor_decode(filters.cursor)
            q = q.or_(f"received_at.lt.{rt},and(received_at.eq.{rt},id.lt.{eid})")

        if filters.triage_category:
            q = q.order("received_at", desc=True).order("id", desc=True)
        else:
            # Supabase/PostgREST cannot express CASE ordering directly here.
            # Keep the DB order deterministic, then apply the Issue 2 triage priority below.
            q = q.order("received_at", desc=True).order("id", desc=True)
        q = q.limit(limit + 1)
        return q.execute().data or []

    rows = await asyncio.to_thread(_fetch)
    if not filters.triage_category:
        priority = {
            "action_required": 1,
            "worth_reading": 2,
            "auto_archive": 3,
        }
        rows.sort(
            key=lambda row: (
                priority.get(row.get("ai_category") or row.get("triage_category"), 4),
                -(datetime.fromisoformat(row["received_at"].replace("Z", "+00:00")).timestamp()
                  if row.get("received_at") else 0),
                str(row.get("id", "")),
            )
        )

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
            .select("*, connected_accounts(color,email_address)")
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


async def update_email(email_id: UUID, user_id: UUID, patch: EmailUpdate) -> Email | None:
    existing = await get_email(email_id, user_id)
    if existing is None:
        return None

    changes: dict[str, Any] = {}
    if patch.is_archived is not None:
        changes["is_archived"] = patch.is_archived
    if patch.pickup_used is not None:
        changes["pickup_used"] = patch.pickup_used
    if not changes:
        return existing

    def _update() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("emails")
            .update(changes)
            .eq("id", str(email_id))
            .eq("user_id", str(user_id))
            .select("*, connected_accounts(color,email_address)")
            .maybe_single()
            .execute()
        )
        return result.data

    row = await asyncio.to_thread(_update)
    _clear_counts_cache(user_id)
    return _row_to_email(row) if row else None


async def get_email_counts(user_id: UUID) -> EmailCounts:
    now = datetime.now(timezone.utc)
    cached = _counts_cache.get(user_id)
    if cached and now - cached[0] < _COUNTS_CACHE_TTL:
        return cached[1]

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("emails")
            .select("ai_category")
            .eq("user_id", str(user_id))
            .eq("is_archived", False)
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    counts = EmailCounts(
        all=len(rows),
        action_required=sum(1 for row in rows if row.get("ai_category") == "action_required"),
        worth_reading=sum(1 for row in rows if row.get("ai_category") == "worth_reading"),
        auto_archive=sum(1 for row in rows if row.get("ai_category") == "auto_archive"),
    )
    _counts_cache[user_id] = (now, counts)
    return counts
