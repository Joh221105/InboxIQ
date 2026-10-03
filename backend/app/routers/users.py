from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import UserClaims, get_current_user
from app.db.users import delete_user_email_data, get_user, update_user_settings
from app.models.user import EmailDataDeleteCounts, User, UserSettingsUpdate
from app.services.retriage import start_retriage

router = APIRouter(prefix="/users", tags=["users"])

ContextValue = Literal["Job Hunting", "Shopping", "School Application", "Daily"]


class UpdateContextBody(BaseModel):
    context: ContextValue


class UpdateContextResponse(BaseModel):
    user: User
    job_id: str
    total: int


@router.get("/me")
async def get_me(claims: UserClaims = Depends(get_current_user)) -> User:
    return await get_user(claims.user_id)


@router.patch("/me/context")
async def patch_context(
    body: UpdateContextBody,
    claims: UserClaims = Depends(get_current_user),
) -> UpdateContextResponse:
    job = await start_retriage(claims.user_id, body.context)
    user = await get_user(claims.user_id)
    return UpdateContextResponse(user=user, job_id=job.job_id, total=job.total)


@router.patch("/me/settings")
async def patch_settings(
    body: UserSettingsUpdate,
    claims: UserClaims = Depends(get_current_user),
) -> User:
    return await update_user_settings(claims.user_id, body)


@router.delete("/me/email-data")
async def delete_email_data(
    claims: UserClaims = Depends(get_current_user),
) -> EmailDataDeleteCounts:
    return await delete_user_email_data(claims.user_id)
