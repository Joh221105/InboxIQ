from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.core.clock import utc_now

JobStatus = Literal["running", "done", "failed"]


@dataclass
class Job:
    """Progress of a long-running job for one user."""

    job_id: str
    user_id: UUID
    total: int
    processed: int = 0
    status: JobStatus = "running"
    created_at: datetime = field(default_factory=utc_now)


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    processed: int
    total: int

    @classmethod
    def from_job(cls, job: Job) -> JobStatusResponse:
        return cls(job_id=job.job_id, status=job.status, processed=job.processed, total=job.total)
