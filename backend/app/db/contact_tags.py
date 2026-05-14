from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from app.db.supabase import get_service_client
from app.models.contact_tag import ContactTag


class UniqueViolation(Exception):
    pass


def _row_to_tag(row: dict[str, Any]) -> ContactTag:
    return ContactTag(**row)


async def list_user_tags(user_id: UUID) -> list[ContactTag]:
    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("contact_tags")
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_tag(r) for r in rows]


async def create_tag(
    user_id: UUID,
    identifier: str,
    tag: str,
    custom_label: str | None,
    color: str,
) -> ContactTag:
    def _insert() -> dict[str, Any]:
        result = (
            get_service_client()
            .table("contact_tags")
            .insert(
                {
                    "user_id": str(user_id),
                    "identifier": identifier,
                    "tag": tag,
                    "custom_label": custom_label,
                    "color": color,
                }
            )
            .select("*")
            .single()
            .execute()
        )
        return result.data

    try:
        row = await asyncio.to_thread(_insert)
        return _row_to_tag(row)
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg or "23505" in msg:
            raise UniqueViolation("duplicate identifier for user") from exc
        raise


async def get_tag(tag_id: UUID, user_id: UUID) -> ContactTag | None:
    def _fetch() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("contact_tags")
            .select("*")
            .eq("id", str(tag_id))
            .eq("user_id", str(user_id))
            .maybe_single()
            .execute()
        )
        return result.data

    row = await asyncio.to_thread(_fetch)
    return _row_to_tag(row) if row else None


async def delete_tag(tag_id: UUID, user_id: UUID) -> bool:
    def _delete() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("contact_tags")
            .delete()
            .eq("id", str(tag_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return result.data or []

    deleted = await asyncio.to_thread(_delete)
    return len(deleted) > 0


async def list_domain_tag_ids(user_id: UUID) -> list[str]:
    """Return IDs of all domain-style tags (identifier starts with @) for this user."""

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("contact_tags")
            .select("id")
            .eq("user_id", str(user_id))
            .like("identifier", "@%")
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [r["id"] for r in rows]


async def count_emails_for_identifier(user_id: UUID, identifier: str) -> int:
    """Count emails matching the identifier (full-email or domain)."""

    def _fetch() -> list[dict[str, Any]]:
        q = (
            get_service_client()
            .table("emails")
            .select("id")
            .eq("user_id", str(user_id))
        )
        if identifier.startswith("@"):
            q = q.ilike("sender", f"%{identifier}")
        else:
            q = q.ilike("sender", identifier)
        result = q.execute()
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return len(rows)


async def apply_retroactive_sync(
    tag_id: UUID,
    user_id: UUID,
    identifier: str,
) -> int:
    """
    Set contact_tag_id on matching emails, respecting specificity.
    Full-email tags overwrite anything; domain tags only overwrite NULL or other domain tags.
    Returns number of emails updated.
    """
    if identifier.startswith("@"):
        domain_ids = await list_domain_tag_ids(user_id)

        def _update_domain() -> list[dict[str, Any]]:
            q = (
                get_service_client()
                .table("emails")
                .update({"contact_tag_id": str(tag_id)})
                .eq("user_id", str(user_id))
                .ilike("sender", f"%{identifier}")
            )
            if domain_ids:
                null_or_domain = ",".join(f"contact_tag_id.eq.{tid}" for tid in domain_ids)
                q = q.or_(f"contact_tag_id.is.null,{null_or_domain}")
            else:
                q = q.is_("contact_tag_id", "null")
            return q.execute().data or []

        rows = await asyncio.to_thread(_update_domain)
    else:
        def _update_full() -> list[dict[str, Any]]:
            result = (
                get_service_client()
                .table("emails")
                .update({"contact_tag_id": str(tag_id)})
                .eq("user_id", str(user_id))
                .ilike("sender", identifier)
                .execute()
            )
            return result.data or []

        rows = await asyncio.to_thread(_update_full)

    return len(rows)
