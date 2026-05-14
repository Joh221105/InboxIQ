# backend/app/db/emails.py
from __future__ import annotations

import asyncio
import base64
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from app.db.supabase import get_service_client
from app.models.email import (
    ContactTagInfo,
    Email,
    EmailCounts,
    EmailFilters,
    EmailListPage,
    EmailUpdate,
    ParsedEmail,
    PickupCodeRow,
)
from app.models.ai import Digest, StoredDigest
from app.services.triage import TriageResult

_COUNTS_CACHE_TTL = timedelta(seconds=30)
_counts_cache: dict[UUID, tuple[datetime, EmailCounts]] = {}

_EMAIL_SELECT = "*, connected_accounts(color,email_address), contact_tags(tag,custom_label,color)"


def _cursor_encode(received_at: datetime, email_id: UUID) -> str:
    raw = f"{received_at.isoformat()}|{email_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _cursor_decode(cursor: str) -> tuple[str, str]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    rt, eid = raw.split("|", 1)
    return rt, eid


def _build_contact_tag(row_tag: dict | None) -> ContactTagInfo | None:
    if not row_tag:
        return None
    label = row_tag.get("custom_label") or row_tag["tag"].capitalize()
    return ContactTagInfo(label=label, color=row_tag.get("color") or "#6b7280")


def _row_to_email(row: dict[str, Any]) -> Email:
    nested = row.pop("connected_accounts", None) or {}
    account_color = nested.get("color") if isinstance(nested, dict) else None
    account_email = nested.get("email_address") if isinstance(nested, dict) else None
    raw_tag = row.pop("contact_tags", None)
    if "ai_category" in row and "triage_category" not in row:
        row["triage_category"] = row.get("ai_category")
    if "sender" in row and "sender_email" not in row:
        row["sender_email"] = row.get("sender")
    raw_items = row.get("action_items")
    if raw_items is None:
        row["action_items"] = []
    return Email(
        **row,
        account_color=account_color,
        account_email=account_email,
        contact_tag=_build_contact_tag(raw_tag),
    )


def _row_to_pickup_code(row: dict[str, Any]) -> PickupCodeRow:
    data = dict(row)
    data["email_id"] = data.pop("email_id", data.pop("id", None))
    if "sender" in data and "sender_email" not in data:
        data["sender_email"] = data.get("sender")
    return PickupCodeRow(**data)


def _clear_counts_cache(user_id: UUID) -> None:
    _counts_cache.pop(user_id, None)


def _date_value(value: date | None) -> str | None:
    return value.isoformat() if value else None


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
            .select(_EMAIL_SELECT)
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

        if filters.has_deadline:
            q = q.not_("deadline_extracted", "is", "null")

        if filters.deadline_after:
            q = q.gte("deadline_extracted", filters.deadline_after.isoformat())

        if filters.deadline_before:
            q = q.lte("deadline_extracted", filters.deadline_before.isoformat())

        if filters.cursor:
            rt, eid = _cursor_decode(filters.cursor)
            q = q.or_(f"received_at.lt.{rt},and(received_at.eq.{rt},id.lt.{eid})")

        if filters.order == "deadline_asc":
            q = q.order("deadline_extracted", desc=False, nullsfirst=False).order("received_at", desc=True)
        elif filters.triage_category:
            q = q.order("received_at", desc=True).order("id", desc=True)
        else:
            # Supabase/PostgREST cannot express CASE ordering directly here.
            # Keep the DB order deterministic, then apply the Issue 2 triage priority below.
            q = q.order("received_at", desc=True).order("id", desc=True)
        q = q.limit(limit + 1)
        return q.execute().data or []

    rows = await asyncio.to_thread(_fetch)
    if not filters.triage_category and filters.order == "received_desc":
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
            .select(_EMAIL_SELECT)
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
        changes["pickup_used_at"] = datetime.now(timezone.utc).isoformat() if patch.pickup_used else None
    if not changes:
        return existing

    def _update() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("emails")
            .update(changes)
            .eq("id", str(email_id))
            .eq("user_id", str(user_id))
            .select(_EMAIL_SELECT)
            .maybe_single()
            .execute()
        )
        return result.data

    row = await asyncio.to_thread(_update)
    _clear_counts_cache(user_id)
    return _row_to_email(row) if row else None


async def list_pickup_codes(
    user_id: UUID,
    used: bool,
    include_expired: bool = False,
) -> list[PickupCodeRow]:
    today = date.today().isoformat()

    def _fetch() -> list[dict[str, Any]]:
        q = (
            get_service_client()
            .table("emails")
            .select(
                "id,pickup_code,pickup_expiry,pickup_used_at,retailer,locker_location,"
                "sender,subject,received_at,connected_accounts!inner(user_id)"
            )
            .eq("connected_accounts.user_id", str(user_id))
            .eq("is_pickup_code", True)
            .not_("pickup_code", "is", "null")
            .eq("pickup_used", used)
        )
        if not include_expired:
            q = q.or_(f"pickup_expiry.is.null,pickup_expiry.gte.{today}")
        return q.order("pickup_code", desc=False).order("received_at", desc=True).execute().data or []

    rows = await asyncio.to_thread(_fetch)
    deduped: list[PickupCodeRow] = []
    seen_codes: set[str] = set()
    for row in rows:
        code = row.get("pickup_code")
        if not code or code in seen_codes:
            continue
        if not include_expired:
            expiry = row.get("pickup_expiry")
            if expiry is not None and expiry < today:
                continue
        seen_codes.add(code)
        deduped.append(_row_to_pickup_code(row))
    return deduped


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


async def apply_triage_result(email_id: UUID, result: TriageResult) -> None:
    changes: dict[str, Any] = {
        "ai_summary": result.summary,
        "ai_category": result.category,
        "triage_context": result.triage_context,
        "deadline_extracted": _date_value(result.deadline_extracted),
        "action_items": result.action_items or [],
        "is_pickup_code": result.is_pickup_code,
        "pickup_code": result.pickup_code,
        "pickup_expiry": _date_value(result.pickup_expiry),
        "retailer": result.retailer,
        "locker_location": result.locker_location,
        "ai_processed": True,
        "last_ai_attempt_at": datetime.now(timezone.utc).isoformat(),
    }

    def _update() -> None:
        get_service_client().table("emails").update(changes).eq("id", str(email_id)).execute()
        get_service_client().rpc("increment_ai_attempts", {"p_email_id": str(email_id)}).execute()

    await asyncio.to_thread(_update)


async def mark_ai_failed(email_id: UUID) -> int:
    now = datetime.now(timezone.utc).isoformat()

    def _update() -> int:
        result = (
            get_service_client()
            .table("emails")
            .update({"last_ai_attempt_at": now})
            .eq("id", str(email_id))
            .select("ai_attempts")
            .maybe_single()
            .execute()
        )
        current = (result.data or {}).get("ai_attempts") or 0
        attempts = int(current) + 1
        changes: dict[str, Any] = {"ai_attempts": attempts, "last_ai_attempt_at": now}
        if attempts >= 3:
            changes.update(
                {
                    "ai_processed": True,
                    "ai_category": "worth_reading",
                    "ai_summary": "(AI unavailable)",
                }
            )
        get_service_client().table("emails").update(changes).eq("id", str(email_id)).execute()
        return attempts

    return await asyncio.to_thread(_update)


async def list_unprocessed_emails(limit: int = 10) -> list[Email]:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("emails")
            .select(_EMAIL_SELECT)
            .eq("ai_processed", False)
            .or_(f"last_ai_attempt_at.is.null,last_ai_attempt_at.lt.{cutoff.isoformat()}")
            .order("received_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_email(row) for row in rows]


async def list_emails_for_retriage(user_id: UUID, limit: int = 100) -> list[Email]:
    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("emails")
            .select(_EMAIL_SELECT)
            .eq("user_id", str(user_id))
            .eq("is_read", False)
            .eq("is_archived", False)
            .order("received_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_email(row) for row in rows]


async def update_email_triage_only(
    email_id: UUID,
    category: str,
    summary: str,
    context: str,
) -> None:
    def _update() -> None:
        get_service_client().table("emails").update(
            {
                "ai_category": category,
                "ai_summary": summary,
                "triage_context": context,
                "ai_processed": True,
            }
        ).eq("id", str(email_id)).execute()

    await asyncio.to_thread(_update)


async def list_action_required_recent(user_id: UUID, hours: int = 24) -> list[Email]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("emails")
            .select(_EMAIL_SELECT)
            .eq("user_id", str(user_id))
            .eq("ai_category", "action_required")
            .gte("received_at", since.isoformat())
            .order("received_at", desc=True)
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_email(row) for row in rows]


async def list_upcoming_deadlines(user_id: UUID, days: int = 7) -> list[Email]:
    today = date.today()
    end = today + timedelta(days=days)

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("emails")
            .select(_EMAIL_SELECT)
            .eq("user_id", str(user_id))
            .gte("deadline_extracted", today.isoformat())
            .lte("deadline_extracted", end.isoformat())
            .order("deadline_extracted", desc=False)
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_email(row) for row in rows]


async def get_digest(user_id: UUID, digest_date: date) -> StoredDigest | None:
    def _fetch() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("daily_digests")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("digest_date", digest_date.isoformat())
            .maybe_single()
            .execute()
        )
        return result.data

    data = await asyncio.to_thread(_fetch)
    if not data:
        return None
    data["payload"] = Digest.model_validate(data["payload"])
    return StoredDigest.model_validate(data)


async def upsert_digest(user_id: UUID, digest_date: date, digest: Digest) -> None:
    payload = {
        "user_id": str(user_id),
        "digest_date": digest_date.isoformat(),
        "payload": digest.model_dump(mode="json"),
        "degraded": digest.degraded,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    def _upsert() -> None:
        get_service_client().table("daily_digests").upsert(payload).execute()

    await asyncio.to_thread(_upsert)
