from __future__ import annotations

import logging
import random
from uuid import UUID

from app.core.background import spawn
from app.db import contact_tags as db
from app.models.contact_tag import ContactTagCreate, CreateContactResponse
from app.models.job import Job
from app.services.jobs import JobRegistry

logger = logging.getLogger(__name__)

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


CONTACT_TAG_JOBS = JobRegistry()


async def apply_retroactive_async(
    tag_id: UUID,
    user_id: UUID,
    identifier: str,
) -> str:
    total = await db.count_emails_for_identifier(user_id, identifier)
    job = CONTACT_TAG_JOBS.create(user_id, total=total)
    spawn(
        _process_retroactive(job, tag_id, user_id, identifier),
        name=f"contact-retroactive:{job.job_id}",
    )
    return job.job_id


async def _process_retroactive(
    job: Job,
    tag_id: UUID,
    user_id: UUID,
    identifier: str,
) -> None:
    try:
        updated = await db.apply_retroactive_sync(tag_id, user_id, identifier)
        job.processed = updated
        job.status = "done"
    except Exception:
        logger.exception("retroactive tagging failed for tag %s", tag_id)
        job.status = "failed"


async def tag_contact(user_id: UUID, body: ContactTagCreate) -> CreateContactResponse:
    """Create a tag and apply it to past emails.

    Small backfills run inline; large ones run as a background job.
    """
    color = body.color or DEFAULT_COLORS.get(body.tag) or random.choice(CUSTOM_PALETTE)
    tag = await db.create_tag(
        user_id=user_id,
        identifier=body.identifier,
        tag=body.tag,
        custom_label=body.custom_label,
        color=color,
    )
    count = await db.count_emails_for_identifier(user_id, body.identifier)
    if count <= SYNC_THRESHOLD:
        await db.apply_retroactive_sync(tag.id, user_id, body.identifier)
        return CreateContactResponse(tag=tag, retroactive_count=count, job_id=None)
    job_id = await apply_retroactive_async(tag.id, user_id, body.identifier)
    return CreateContactResponse(tag=tag, retroactive_count=count, job_id=job_id)
