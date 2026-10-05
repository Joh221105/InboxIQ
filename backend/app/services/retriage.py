from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from uuid import UUID

from app.core.background import spawn
from app.core.clock import utc_now
from app.core.errors import RateLimitedError
from app.db.emails import list_emails_for_retriage, update_email_triage_only
from app.db.users import update_default_context
from app.models.ai import TriageResponse
from app.models.email import Email
from app.models.job import Job
from app.models.user import ContextMode
from app.prompts.triage import TRIAGE_PROMPTS
from app.services.ai_client import call_json
from app.services.jobs import JobRegistry
from app.services.triage import triage_message

logger = logging.getLogger(__name__)

RETRIAGE_JOBS = JobRegistry()
RATE_LIMIT_SECONDS = 60
_RATE_LIMIT_MEMORY = timedelta(hours=1)
_last_request_at: dict[UUID, datetime] = {}


def _evict_stale_rate_limits() -> None:
    cutoff = utc_now() - _RATE_LIMIT_MEMORY
    for user_id in [uid for uid, ts in _last_request_at.items() if ts < cutoff]:
        del _last_request_at[user_id]


async def start_retriage(user_id: UUID, context: ContextMode) -> Job:
    _evict_stale_rate_limits()
    now = utc_now()
    last = _last_request_at.get(user_id)
    if last is not None:
        elapsed = (now - last).total_seconds()
        if elapsed < RATE_LIMIT_SECONDS:
            raise RateLimitedError(math.ceil(RATE_LIMIT_SECONDS - elapsed))
    _last_request_at[user_id] = now

    await update_default_context(user_id, context)
    emails = await list_emails_for_retriage(user_id, limit=100)
    job = RETRIAGE_JOBS.create(user_id, total=len(emails))
    spawn(_process_retriage(job, emails, context), name=f"retriage:{job.job_id}")
    return job


async def _process_retriage(job: Job, emails: list[Email], context: ContextMode) -> None:
    try:
        for email in emails:
            try:
                triage = await call_json(
                    system=TRIAGE_PROMPTS[context],
                    user=triage_message(email),
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
