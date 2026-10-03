from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from app.db import contact_tags as db

VALID_TAG_TYPES = {"professor", "friend", "recruiter", "custom"}

DEFAULT_COLORS: dict[str, str] = {
    "professor": "#3B82F6",
    "friend": "#10B981",
    "recruiter": "#F59E0B",
}

CUSTOM_PALETTE = [
    "#8B5CF6",
    "#EC4899",
    "#14B8A6",
    "#F97316",
    "#06B6D4",
    "#A855F7",
    "#84CC16",
    "#F43F5E",
]

SYNC_THRESHOLD = 100


def normalize_identifier(s: str) -> str:
    s = s.strip().lower()
    if not s:
        raise ValueError("identifier cannot be empty")
    if s.startswith("@"):
        domain = s[1:]
        if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", domain):
            raise ValueError(f"invalid domain identifier: {s!r}")
        return s
    if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", s):
        raise ValueError(f"invalid email identifier: {s!r}")
    return s


async def find_contact_tag(user_id: UUID, sender_email: str) -> UUID | None:
    """Return the most-specific matching tag id (full-email beats domain)."""
    sender = sender_email.lower()
    tags = await db.list_user_tags(user_id)

    full_match: UUID | None = None
    domain_match: UUID | None = None

    for tag in tags:
        ident = tag.identifier
        if not ident.startswith("@") and ident == sender:
            full_match = tag.id
            break
        if ident.startswith("@") and sender.endswith(ident):
            domain_match = tag.id

    return full_match if full_match else domain_match


@dataclass
class ContactTagJob:
    job_id: str
    user_id: UUID
    total: int
    processed: int = 0
    status: Literal["running", "done", "failed"] = "running"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


JOBS: dict[str, ContactTagJob] = {}
_JOB_TTL_SECONDS = 3600


def _evict_stale_contact_jobs() -> None:
    cutoff = datetime.now(UTC) - timedelta(seconds=_JOB_TTL_SECONDS)
    stale = [
        job_id
        for job_id, job in list(JOBS.items())
        if job.status in ("done", "failed") and job.created_at < cutoff
    ]
    for job_id in stale:
        JOBS.pop(job_id, None)


async def apply_retroactive_async(
    tag_id: UUID,
    user_id: UUID,
    identifier: str,
) -> str:
    _evict_stale_contact_jobs()
    job_id = uuid.uuid4().hex
    total = await db.count_emails_for_identifier(user_id, identifier)
    job = ContactTagJob(job_id=job_id, user_id=user_id, total=total)
    JOBS[job_id] = job
    asyncio.create_task(_process_retroactive(job, tag_id, user_id, identifier))
    return job_id


async def _process_retroactive(
    job: ContactTagJob,
    tag_id: UUID,
    user_id: UUID,
    identifier: str,
) -> None:
    try:
        updated = await db.apply_retroactive_sync(tag_id, user_id, identifier)
        job.processed = updated
        job.status = "done"
    except Exception:
        job.status = "failed"
