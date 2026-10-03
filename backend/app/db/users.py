from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from postgrest.types import CountMethod

from app.core.errors import NotFoundError
from app.db.supabase import get_service_client
from app.models.user import ContextMode, EmailDataDeleteCounts, User, UserSettingsUpdate


def _user_or_404(rows: list[dict[str, Any]]) -> User:
    if not rows:
        raise NotFoundError("User not found.")
    return User(**rows[0])


async def get_user(user_id: UUID) -> User:
    def _fetch() -> list[dict[str, Any]]:
        result = get_service_client().table("users").select("*").eq("id", str(user_id)).execute()
        return result.data or []

    return _user_or_404(await asyncio.to_thread(_fetch))


async def _update_user(user_id: UUID, changes: dict[str, Any]) -> User:
    def _update() -> list[dict[str, Any]]:
        # PostgREST returns the updated rows (Prefer: return=representation).
        result = (
            get_service_client().table("users").update(changes).eq("id", str(user_id)).execute()
        )
        return result.data or []

    return _user_or_404(await asyncio.to_thread(_update))


async def update_default_context(user_id: UUID, context: ContextMode) -> User:
    return await _update_user(user_id, {"default_context": context})


async def update_user_settings(user_id: UUID, settings: UserSettingsUpdate) -> User:
    changes: dict[str, Any] = {}
    if "notification_tag_preferences" in settings.model_fields_set:
        changes["notification_tag_preferences"] = settings.notification_tag_preferences or {}
    if "data_retention_days" in settings.model_fields_set:
        changes["data_retention_days"] = settings.data_retention_days

    if not changes:
        return await get_user(user_id)
    return await _update_user(user_id, changes)


async def delete_user_email_data(user_id: UUID) -> EmailDataDeleteCounts:
    def _delete_table(table: str) -> int:
        result = (
            get_service_client()
            .table(table)
            .delete(count=CountMethod.exact)
            .eq("user_id", str(user_id))
            .execute()
        )
        return int(result.count or 0)

    emails_count, daily_digests_count, ai_usage_count = await asyncio.gather(
        asyncio.to_thread(_delete_table, "emails"),
        asyncio.to_thread(_delete_table, "daily_digests"),
        asyncio.to_thread(_delete_table, "ai_usage"),
    )
    return EmailDataDeleteCounts(
        emails=emails_count,
        daily_digests=daily_digests_count,
        ai_usage=ai_usage_count,
    )
