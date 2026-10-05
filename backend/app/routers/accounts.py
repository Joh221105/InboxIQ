from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends

from app.core.auth import UserClaims, get_current_user
from app.core.errors import ConflictError, NotFoundError
from app.db.connected_accounts import delete_account, get_account, list_user_accounts
from app.models.connected_account import AccountPublic, ConnectedAccount
from app.models.email import SyncResult
from app.services.gmail_oauth import revoke
from app.services.gmail_sync import sync_account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


async def _owned_account(account_id: UUID, user_id: UUID) -> ConnectedAccount:
    account = await get_account(account_id)
    if account.user_id != user_id:
        raise NotFoundError("Account not found.")
    return account


@router.get("")
async def list_accounts(claims: UserClaims = Depends(get_current_user)) -> list[AccountPublic]:
    accounts = await list_user_accounts(claims.user_id)
    return [AccountPublic.model_validate(a, from_attributes=True) for a in accounts]


@router.delete("/{account_id}", status_code=204, response_model=None)
async def disconnect_account(
    account_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> None:
    account = await _owned_account(account_id, claims.user_id)
    try:
        await revoke(account.oauth_token.refresh_token)
    except httpx.HTTPError as exc:
        # Revocation is best-effort; the account is removed regardless.
        logger.warning("failed to revoke token for account %s: %s", account_id, exc)
    await delete_account(account_id)


@router.post("/{account_id}/sync")
async def trigger_sync(
    account_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> SyncResult:
    account = await _owned_account(account_id, claims.user_id)
    if account.disconnected_at is not None:
        raise ConflictError(
            "Reconnect this account to resume syncing.", code="account_disconnected"
        )
    return await sync_account(account_id)
