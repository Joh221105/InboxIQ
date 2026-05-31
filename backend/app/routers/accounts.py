# backend/app/routers/accounts.py
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse

from app.core.auth import UserClaims, get_current_user
from app.db.connected_accounts import delete_account, get_account, list_user_accounts
from app.models.connected_account import AccountPublic
from app.models.email import SyncResult
from app.services.gmail_oauth import revoke
from app.services.gmail_sync import sync_account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    claims: UserClaims = Depends(get_current_user),
) -> list[AccountPublic]:
    accounts = await list_user_accounts(claims.user_id)
    return [AccountPublic.model_validate(a) for a in accounts]


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
    except Exception as exc:
        logger.warning("Failed to revoke token for account %s: %s", account_id, exc)
    await delete_account(account_id)
    return Response(status_code=204)


@router.post("/{account_id}/sync", response_model=SyncResult)
async def trigger_sync(
    account_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> SyncResult | JSONResponse:
    account = await get_account(account_id)
    if account.user_id != claims.user_id:
        raise HTTPException(status_code=404)
    if account.disconnected_at is not None:
        return JSONResponse(
            status_code=409,
            content={"reason": "disconnected"},
        )
    return await sync_account(account_id)
