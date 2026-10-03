from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import UserClaims, get_current_user
from app.models.job import JobStatusResponse
from app.services.retriage import RETRIAGE_JOBS

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    claims: UserClaims = Depends(get_current_user),
) -> JobStatusResponse:
    return JobStatusResponse.from_job(RETRIAGE_JOBS.get_for_user(job_id, claims.user_id))
