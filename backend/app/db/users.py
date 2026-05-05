from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import HTTPException

from app.db.supabase import get_service_client
from app.models.user import User


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
    def _update() -> dict | None:
        result = (
            get_service_client()
            .table("users")
            .update({"default_context": context})
            .eq("id", str(user_id))
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    data = await asyncio.to_thread(_update)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)
