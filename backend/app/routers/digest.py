from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import UserClaims, get_current_user
from app.models.ai import Digest
from app.services.digest import get_or_create_today_digest

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("/today")
async def get_today_digest(claims: UserClaims = Depends(get_current_user)) -> Digest:
    return await get_or_create_today_digest(claims.user_id)
