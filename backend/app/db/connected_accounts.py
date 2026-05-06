from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from app.db.supabase import get_service_client
from app.models.connected_account import ConnectedAccount, OAuthTokens


def _row_to_account(row: dict) -> ConnectedAccount:
    raw_token = row.get("oauth_token") or {}
    row = {**row, "oauth_token": OAuthTokens(**raw_token)}
    return ConnectedAccount(**row)


async def upsert_account(
    user_id: UUID,
    email_address: str,
    provider: str,
    oauth_token: OAuthTokens,
) -> ConnectedAccount:
    def _upsert() -> dict:
        client = get_service_client()
        result = client.table("connected_accounts").upsert(
            {
                "user_id": str(user_id),
                "email_address": email_address,
                "provider": provider,
                "oauth_token": oauth_token.model_dump(mode="json"),
                "disconnected_at": None,
                "disconnected_reason": None,
            },
            on_conflict="user_id,email_address",
        ).execute()
        row = result.data[0]
        if row.get("color") is None:
            client.rpc(
                "assign_account_color",
                {"p_user_id": str(user_id), "p_account_id": row["id"]},
            ).execute()
            row = (
                client.table("connected_accounts")
                .select("*")
                .eq("id", row["id"])
                .single()
                .execute()
                .data
            )
        return row

    row = await asyncio.to_thread(_upsert)
    return _row_to_account(row)


async def get_account(account_id: UUID) -> ConnectedAccount:
    def _fetch() -> dict | None:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .eq("id", str(account_id))
            .maybe_single()
            .execute()
        )
        return result.data if result is not None else None  # type: ignore[return-value]

    row = await asyncio.to_thread(_fetch)
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return _row_to_account(row)


async def list_user_accounts(user_id: UUID) -> list[ConnectedAccount]:
    def _fetch() -> list[dict]:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at")
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_account(r) for r in rows]


async def update_oauth_token(account_id: UUID, new_token: OAuthTokens) -> ConnectedAccount:
    def _update() -> dict:
        result = (
            get_service_client()
            .table("connected_accounts")
            .update({"oauth_token": new_token.model_dump(mode="json")})
            .eq("id", str(account_id))
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else {}

    row = await asyncio.to_thread(_update)
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return _row_to_account(row)


async def mark_disconnected(account_id: UUID, reason: str) -> None:
    def _update() -> None:
        get_service_client().table("connected_accounts").update(
            {
                "disconnected_at": datetime.now(timezone.utc).isoformat(),
                "disconnected_reason": reason,
            }
        ).eq("id", str(account_id)).execute()

    await asyncio.to_thread(_update)


async def delete_account(account_id: UUID) -> None:
    def _delete() -> None:
        get_service_client().table("connected_accounts").delete().eq(
            "id", str(account_id)
        ).execute()

    await asyncio.to_thread(_delete)
