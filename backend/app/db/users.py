from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from app.db.supabase import get_service_client
from app.models.user import EmailDataDeleteCounts, User, UserSettingsUpdate


async def get_user(user_id: UUID) -> User:
    def _fetch() -> dict | None:
        result = (
            get_service_client()
            .table("users")
            .select("*")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )
        return result.data if result is not None else None  # type: ignore[return-value]

    data = await asyncio.to_thread(_fetch)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)


async def update_default_context(user_id: UUID, context: str) -> User:
    def _update() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("users")
            .update({"default_context": context})
            .eq("id", str(user_id))
            .select("*")
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    data = await asyncio.to_thread(_update)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)


async def update_user_settings(user_id: UUID, settings: UserSettingsUpdate) -> User:
    changes: dict[str, object] = {}
    if "notification_tag_preferences" in settings.model_fields_set:
        changes["notification_tag_preferences"] = settings.notification_tag_preferences or {}
    if "data_retention_days" in settings.model_fields_set:
        changes["data_retention_days"] = settings.data_retention_days

    if not changes:
        return await get_user(user_id)

    def _update() -> dict | None:
        result = (
            get_service_client()
            .table("users")
            .update(changes)
            .eq("id", str(user_id))
            .select("*")          # required: without this, supabase-py returns data=[]
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    data = await asyncio.to_thread(_update)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)


async def delete_user_email_data(user_id: UUID) -> EmailDataDeleteCounts:
    def _delete_table(table: str) -> int:
        result = (
            get_service_client()
            .table(table)
            .delete(count="exact")
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
