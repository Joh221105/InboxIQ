from __future__ import annotations

import asyncio
import logging
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from app.db.emails import list_emails_for_retriage, update_email_triage_only
from app.db.users import update_default_context
from app.models.ai import TriageResponse
from app.models.email import Email
from app.prompts.triage import TRIAGE_PROMPTS
from app.services.openai_client import call_json

logger = logging.getLogger(__name__)


@dataclass
class RetriageJob:
    job_id: str
    user_id: UUID
    total: int
    processed: int = 0
    status: Literal["running", "done", "failed"] = "running"


JOBS: dict[str, RetriageJob] = {}
RATE_LIMIT_SECONDS = 60
_last_request_at: dict[UUID, datetime] = {}


class RateLimited(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after = retry_after_seconds


async def start_retriage(user_id: UUID, context: str) -> RetriageJob:
    now = datetime.now(timezone.utc)
    last = _last_request_at.get(user_id)
    if last:
        elapsed = (now - last).total_seconds()
        if elapsed < RATE_LIMIT_SECONDS:
            raise RateLimited(math.ceil(RATE_LIMIT_SECONDS - elapsed))
    _last_request_at[user_id] = now

    await update_default_context(user_id, context)
    emails = await list_emails_for_retriage(user_id, limit=100)
    job = RetriageJob(job_id=uuid.uuid4().hex, user_id=user_id, total=len(emails))
    JOBS[job.job_id] = job
    asyncio.create_task(_process_retriage(job, emails, context))
    return job


async def _process_retriage(job: RetriageJob, emails: list[Email], context: str) -> None:
    try:
        for email in emails:
            try:
                body = email.body_text or ""
                user_msg = (
                    f"From: {email.sender or ''}\n"
                    f"Subject: {email.subject or ''}\n"
                    f"Body: {body[:4000]}"
                )
                triage = await call_json(
                    system=TRIAGE_PROMPTS[context],
                    user=user_msg,
                    response_model=TriageResponse,
                    kind="retriage",
                    user_id=email.user_id,
                    email_id=email.id,
                )
                await update_email_triage_only(email.id, triage.category, triage.summary, context)
            except Exception:
                logger.exception("retriage one email failed")
            job.processed += 1
        job.status = "done"
    except Exception:
        logger.exception("retriage job crashed")
        job.status = "failed"
