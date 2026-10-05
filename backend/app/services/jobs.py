"""In-memory progress tracking for long-running user jobs.

Jobs live only in this process: they are lost on restart and are not shared
across replicas. That is acceptable for the single-instance deployment
described in docs/architecture.md.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import NotFoundError
from app.models.job import Job

__all__ = ["Job", "JobRegistry"]


class JobRegistry:
    def __init__(self, ttl: timedelta = timedelta(hours=1)) -> None:
        self._jobs: dict[str, Job] = {}
        self._ttl = ttl

    def create(self, user_id: UUID, total: int) -> Job:
        self._evict_finished()
        job = Job(job_id=uuid.uuid4().hex, user_id=user_id, total=total)
        self._jobs[job.job_id] = job
        return job

    def get_for_user(self, job_id: str, user_id: UUID) -> Job:
        job = self._jobs.get(job_id)
        if job is None or job.user_id != user_id:
            raise NotFoundError("Job not found.")
        return job

    def clear(self) -> None:
        self._jobs.clear()

    def _evict_finished(self) -> None:
        cutoff = utc_now() - self._ttl
        stale = [
            job_id
            for job_id, job in self._jobs.items()
            if job.status != "running" and job.created_at < cutoff
        ]
        for job_id in stale:
            del self._jobs[job_id]
