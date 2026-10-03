from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.errors import NotFoundError
from app.db.supabase import get_service_client
from app.models.connected_account import ConnectedAccount, OAuthTokens


def _row_to_account(row: dict[str, Any]) -> ConnectedAccount:
    token = OAuthTokens.model_validate(row.get("oauth_token") or {})
    return ConnectedAccount(**{**row, "oauth_token": token})


async def upsert_account(
    user_id: UUID,
    email_address: str,
    provider: str,
    oauth_token: OAuthTokens,
) -> ConnectedAccount:
    def _upsert() -> dict[str, Any]:
        client = get_service_client()
        result = (
            client.table("connected_accounts")
            .upsert(
                {
                    "user_id": str(user_id),
                    "email_address": email_address,
                    "provider": provider,
                    "oauth_token": oauth_token.model_dump(mode="json"),
                    "disconnected_at": None,
                    "disconnected_reason": None,
                },
                on_conflict="user_id,email_address",
            )
            .execute()
        )
        if not result.data:
            raise RuntimeError("upsert returned no data")
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
    def _fetch() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .eq("id", str(account_id))
            .maybe_single()
            .execute()
        )
        return result.data if result is not None else None  # maybe_single(): None when no row

    row = await asyncio.to_thread(_fetch)
    if not row:
        raise NotFoundError("Account not found.")
    return _row_to_account(row)


async def list_user_accounts(user_id: UUID) -> list[ConnectedAccount]:
    def _fetch() -> list[dict[str, Any]]:
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
    def _update() -> dict[str, Any]:
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
        raise NotFoundError("Account not found.")
    return _row_to_account(row)


async def mark_disconnected(account_id: UUID, reason: str) -> None:
    def _update() -> None:
        get_service_client().table("connected_accounts").update(
            {
                "disconnected_at": datetime.now(UTC).isoformat(),
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


async def update_last_synced(account_id: UUID, synced_at: datetime) -> None:
    def _update() -> None:
        get_service_client().table("connected_accounts").update(
            {"last_synced": synced_at.isoformat()}
        ).eq("id", str(account_id)).execute()

    await asyncio.to_thread(_update)


async def list_accounts_due_for_sync() -> list[ConnectedAccount]:
    cutoff = (datetime.now(UTC) - timedelta(minutes=14)).isoformat()

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .is_("disconnected_at", "null")
            .or_(f"last_synced.is.null,last_synced.lt.{cutoff}")
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_account(r) for r in rows]
