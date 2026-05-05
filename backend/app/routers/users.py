from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import UserClaims, get_current_user
from app.db.users import get_user, update_default_context
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

ContextValue = Literal[
    "Job Hunting", "Shopping", "School Application", "Daily"
]


class UpdateContextBody(BaseModel):
    context: ContextValue


@router.get("/me")
async def get_me(claims: UserClaims = Depends(get_current_user)) -> User:
    return await get_user(claims.user_id)


@router.patch("/me/context")
async def patch_context(
    body: UpdateContextBody,
    claims: UserClaims = Depends(get_current_user),
) -> User:
    return await update_default_context(claims.user_id, body.context)
