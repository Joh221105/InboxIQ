# backend/app/routers/accounts.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import UserClaims, get_current_user
from app.db.connected_accounts import delete_account, get_account, list_user_accounts
from app.models.connected_account import AccountPublic
from app.services.gmail_oauth import revoke

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    claims: UserClaims = Depends(get_current_user),
) -> list[AccountPublic]:
    accounts = await list_user_accounts(claims.user_id)
    return [
        AccountPublic(
            id=a.id,
            email_address=a.email_address,
            provider=a.provider,
            color=a.color,
            last_synced=a.last_synced,
            disconnected_at=a.disconnected_at,
        )
        for a in accounts
    ]


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> Response:
    account = await get_account(account_id)
    if account.user_id != claims.user_id:
        raise HTTPException(status_code=404)
    try:
        await revoke(account.oauth_token.refresh_token)
    except Exception:
        pass
    await delete_account(account_id)
    return Response(status_code=204)
