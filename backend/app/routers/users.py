from __future__ import annotations

from typing import Any, Dict, Literal, Union

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.auth import UserClaims, get_current_user
from app.db.users import get_user
from app.models.user import User
from app.services.retriage import RateLimited, start_retriage

router = APIRouter(prefix="/users", tags=["users"])

ContextValue = Literal[
    "Job Hunting", "Shopping", "School Application", "Daily"
]


class UpdateContextBody(BaseModel):
    context: ContextValue


class UpdateContextResponse(BaseModel):
    user: User
    job_id: str
    total: int


@router.get("/me")
async def get_me(claims: UserClaims = Depends(get_current_user)) -> User:
    return await get_user(claims.user_id)


@router.patch("/me/context", response_model=Union[UpdateContextResponse, Dict[str, Any]])
async def patch_context(
    body: UpdateContextBody,
    claims: UserClaims = Depends(get_current_user),
):
    try:
        job = await start_retriage(claims.user_id, body.context)
    except RateLimited as exc:
        return JSONResponse(
            status_code=429,
            content={"reason": "rate_limited", "retry_after_seconds": exc.retry_after},
            headers={"Retry-After": str(exc.retry_after)},
        )
    user = await get_user(claims.user_id)
    return UpdateContextResponse(user=user, job_id=job.job_id, total=job.total)
