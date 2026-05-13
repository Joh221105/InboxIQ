from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.auth import UserClaims, get_current_user
from app.services.retriage import JOBS, RateLimited, start_retriage

router = APIRouter(tags=["triage"])

ContextValue = Literal["Job Hunting", "Shopping", "School Application", "Daily"]


class RetriageBody(BaseModel):
    context: ContextValue


class RetriageStartResponse(BaseModel):
    job_id: str
    total: int


class JobStatusResponse(BaseModel):
    status: Literal["running", "done", "failed"]
    processed: int
    total: int


@router.post("/triage/retriage", response_model=RetriageStartResponse | dict[str, int | str])
async def post_retriage(
    body: RetriageBody,
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
    return RetriageStartResponse(job_id=job.job_id, total=job.total)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    claims: UserClaims = Depends(get_current_user),
):
    job = JOBS.get(job_id)
    if not job or job.user_id != claims.user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(status=job.status, processed=job.processed, total=job.total)
