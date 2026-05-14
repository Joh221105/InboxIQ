from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.auth import UserClaims, get_current_user
from app.db.emails import list_pickup_codes
from app.models.email import PickupCodeListResponse

router = APIRouter(tags=["pickup"])


@router.get("/pickup-codes")
async def get_pickup_codes(
    claims: UserClaims = Depends(get_current_user),
    used: bool = Query(default=False),
    include_expired: bool = Query(default=False),
) -> PickupCodeListResponse:
    items = await list_pickup_codes(claims.user_id, used=used, include_expired=include_expired)
    return PickupCodeListResponse(items=items)
