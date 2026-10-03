from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from postgrest.types import CountMethod

from app.core.clock import utc_now, utc_today
from app.core.errors import BadRequestError
from app.db.supabase import get_service_client
from app.models.ai import Digest, StoredDigest, TriageResult
from app.models.email import (
    ContactTagInfo,
    Email,
    EmailCounts,
    EmailFilters,
    EmailListPage,
    EmailUpdate,
    ParsedEmail,
    PickupCodeRow,
    TriageCategory,
)

_log = logging.getLogger(__name__)

_COUNTS_CACHE_TTL = timedelta(seconds=30)
_MAX_AI_ATTEMPTS = 3
_TRIAGE_RANKS = range(1, 4)  # emails.triage_rank values (migration 022)
_counts_cache: dict[UUID, tuple[datetime, EmailCounts]] = {}

_EMAIL_SELECT = "*, connected_accounts(color,email_address), contact_tags!contact_tag_id(tag,custom_label,color)"


def _sanitize_fts_input(value: str | None) -> str | None:
    """Keep full-text search input plain before passing it to phraseto_tsquery."""
    if not value:
        return None
    cleaned = re.sub(r"[^\w\s]", " ", value)
    collapsed = " ".join(cleaned.split())
    return collapsed or None


@dataclass(frozen=True)
class _Cursor:
    rank: int
    received_at: str
    email_id: str


def _encode_cursor(row: dict[str, Any]) -> str:
    payload = {"r": row["triage_rank"], "t": row["received_at"], "i": row["id"]}
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def _decode_cursor(cursor: str) -> _Cursor:
    """Parse a client-supplied cursor strictly; its values end up in a PostgREST filter."""
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        rank, received_at, email_id = data["r"], data["t"], data["i"]
        if not isinstance(rank, int) or rank not in _TRIAGE_RANKS:
            raise ValueError("cursor rank out of range")
        if not isinstance(received_at, str) or not isinstance(email_id, str):
            raise TypeError("cursor fields must be strings")
        return _Cursor(
            rank=rank,
            received_at=datetime.fromisoformat(received_at).isoformat(),
            email_id=str(UUID(email_id)),
        )
    except (ValueError, KeyError, TypeError) as exc:  # binascii/JSON errors are ValueErrors
        raise BadRequestError("Invalid pagination cursor.", code="invalid_cursor") from exc


def _keyset_filter(cursor: _Cursor) -> str:
    """PostgREST ``or`` filter for rows strictly after *cursor* in
    (triage_rank ASC, received_at DESC, id DESC) order. Timestamps are quoted
    because they contain PostgREST-reserved characters."""
    r, t, i = cursor.rank, cursor.received_at, cursor.email_id
    return (
        f"triage_rank.gt.{r},"
        f'and(triage_rank.eq.{r},received_at.lt."{t}"),'
        f'and(triage_rank.eq.{r},received_at.eq."{t}",id.lt.{i})'
    )


def _build_contact_tag(row_tag: dict | None) -> ContactTagInfo | None:
    if not row_tag:
        return None
    label = row_tag.get("custom_label") or row_tag["tag"].capitalize()
    return ContactTagInfo(label=label, color=row_tag.get("color") or "#6b7280")


def _row_to_email(row: dict[str, Any]) -> Email:
    row = dict(row)
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
    *,
    contact_tag_id: UUID | None = None,
) -> Literal["inserted", "updated"]:
    def _do() -> Literal["inserted", "updated"]:
        result = (
            get_service_client()
            .rpc(
                "upsert_email_record",
                {
                    "p_account_id": str(account_id),
                    "p_user_id": str(user_id),
                    "p_gmail_id": parsed.external_id,
                    "p_subject": parsed.subject,
                    "p_sender": parsed.sender_email,
                    "p_sender_name": parsed.sender_name,
                    "p_body_text": parsed.body_preview,
                    "p_contact_tag_id": str(contact_tag_id) if contact_tag_id else None,
                    "p_received_at": parsed.received_at.isoformat(),
                },
            )
            .execute()
        )
        if result.data not in ("inserted", "updated"):
            raise RuntimeError(f"Unexpected upsert result: {result.data!r}")
        return result.data

    return await asyncio.to_thread(_do)


async def list_emails(filters: EmailFilters) -> EmailListPage:
    """One page of the inbox.

    The default order is triage priority then recency, paginated with a
    keyset cursor; ``deadline_asc`` returns a single, unpaginated page.
    """
    paginated = filters.order == "received_desc"
    if filters.cursor and not paginated:
        raise BadRequestError(
            "Cursors are only supported for received_desc order.", code="invalid_cursor"
        )
    cursor = _decode_cursor(filters.cursor) if filters.cursor else None

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

        if filters.contact_tag_id:
            q = q.eq("contact_tag_id", str(filters.contact_tag_id))

        if filters.triage_category:
            q = q.eq("ai_category", filters.triage_category)

        if filters.since:
            q = q.gte("received_at", filters.since.isoformat())

        if filters.search:
            safe_search = _sanitize_fts_input(filters.search)
            if safe_search:
                q = q.filter("search_tsv", "plfts(english)", safe_search)

        if filters.sender_search:
            q = q.ilike("sender", f"%{filters.sender_search}%")

        if filters.has_deadline:
            q = q.filter("deadline_extracted", "not.is", "null")

        if filters.deadline_after:
            q = q.gte("deadline_extracted", filters.deadline_after.isoformat())

        if filters.deadline_before:
            q = q.lte("deadline_extracted", filters.deadline_before.isoformat())

        if paginated:
            if cursor is not None:
                q = q.or_(_keyset_filter(cursor))
            q = (
                q.order("triage_rank", desc=False)
                .order("received_at", desc=True)
                .order("id", desc=True)
            )
        else:
            q = q.order("deadline_extracted", desc=False, nullsfirst=False).order(
                "received_at", desc=True
            )
        q = q.limit(filters.limit + 1)
        return q.execute().data or []

    rows = await asyncio.to_thread(_fetch)
    page = rows[: filters.limit]
    has_more = paginated and len(rows) > filters.limit
    next_cursor = _encode_cursor(page[-1]) if has_more else None
    return EmailListPage(items=[_row_to_email(r) for r in page], next_cursor=next_cursor)


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
        return result.data if result is not None else None  # maybe_single(): None when no row

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
        changes["pickup_used_at"] = utc_now().isoformat() if patch.pickup_used else None
        if patch.pickup_used:
            changes["is_archived"] = True
    if patch.is_read is not None:
        changes["is_read"] = patch.is_read
    if not changes:
        return existing

    def _update() -> None:
        (
            get_service_client()
            .table("emails")
            .update(changes)
            .eq("id", str(email_id))
            .eq("user_id", str(user_id))
            .execute()
        )

    await asyncio.to_thread(_update)
    _clear_counts_cache(user_id)
    # Re-read so the response includes the joined account and contact-tag fields.
    return await get_email(email_id, user_id)


async def list_pickup_codes(
    user_id: UUID,
    used: bool,
    include_expired: bool = False,
) -> list[PickupCodeRow]:
    today = utc_today().isoformat()

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
            .filter("pickup_code", "not.is", "null")
            .eq("pickup_used", used)
        )
        if not include_expired:
            q = q.or_(f"pickup_expiry.is.null,pickup_expiry.gte.{today}")
        return (
            q.order("pickup_code", desc=False).order("received_at", desc=True).execute().data or []
        )

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
    now = utc_now()
    cached = _counts_cache.get(user_id)
    if cached and now - cached[0] < _COUNTS_CACHE_TTL:
        return cached[1]

    def _count(category: TriageCategory | None) -> int:
        q = (
            get_service_client()
            .table("emails")
            # head=True would skip the body, but postgrest 0.17 then reports count=0;
            # fetch one row instead and read the total from Content-Range.
            .select("id", count=CountMethod.exact)
            .eq("user_id", str(user_id))
            .eq("is_archived", False)
        )
        if category is not None:
            q = q.eq("ai_category", category)
        return q.limit(1).execute().count or 0

    total, action, worth, archive = await asyncio.gather(
        *(
            asyncio.to_thread(_count, category)
            for category in (None, "action_required", "worth_reading", "auto_archive")
        )
    )
    counts = EmailCounts(
        all=total, action_required=action, worth_reading=worth, auto_archive=archive
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
        "last_ai_attempt_at": utc_now().isoformat(),
    }

    def _update() -> None:
        get_service_client().table("emails").update(changes).eq("id", str(email_id)).execute()
        get_service_client().rpc("increment_ai_attempts", {"p_email_id": str(email_id)}).execute()

    await asyncio.to_thread(_update)


async def mark_ai_failed(email_id: UUID) -> int:
    """Record a failed AI attempt; after the third, show a placeholder summary.

    The email stays unprocessed so the worker retries it until the attempt cap
    in `list_unprocessed_emails` stops picking it up.
    """

    def _update() -> int:
        client = get_service_client()
        client.rpc("increment_ai_attempts", {"p_email_id": str(email_id)}).execute()
        row = (
            client.table("emails").select("ai_attempts").eq("id", str(email_id)).single().execute()
        )
        attempts = int((row.data or {}).get("ai_attempts") or 0)
        changes: dict[str, Any] = {"ai_processed": False}
        if attempts >= _MAX_AI_ATTEMPTS:
            changes["ai_summary"] = "(AI unavailable)"
        client.table("emails").update(changes).eq("id", str(email_id)).execute()
        return attempts

    return await asyncio.to_thread(_update)


async def list_unprocessed_emails(limit: int = 10) -> list[Email]:
    cutoff = utc_now() - timedelta(seconds=60)

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("emails")
            .select(_EMAIL_SELECT)
            .eq("ai_processed", False)
            .lt("ai_attempts", _MAX_AI_ATTEMPTS)  # don't retry permanently-failed emails
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
    since = utc_now() - timedelta(hours=hours)

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
    today = utc_today()
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
        try:
            result = (
                get_service_client()
                .table("daily_digests")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("digest_date", digest_date.isoformat())
                .maybe_single()
                .execute()
            )
            return result.data if result is not None else None
        except Exception as exc:
            _log.warning("get_digest query failed (treating as cache miss): %s", exc)
            return None

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
        "generated_at": utc_now().isoformat(),
    }

    def _upsert() -> None:
        get_service_client().table("daily_digests").upsert(payload).execute()

    await asyncio.to_thread(_upsert)
