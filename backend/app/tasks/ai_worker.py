from __future__ import annotations

import asyncio
import dataclasses
import logging
from decimal import Decimal
from uuid import UUID

from app.db.emails import apply_triage_result, list_unprocessed_emails, mark_ai_failed
from app.db.users import get_user
from app.models.ai import TriageResult
from app.services.openai_client import AIInvalidResponse, AIServiceUnavailable
from app.services.triage import triage_email

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
BATCH_COST_CAP_USD = 0.50
WORKER_INTERVAL_SECONDS = 30


async def _apply_with_tag_override(
    email_id: UUID,
    result: TriageResult,
    has_contact_tag: bool,
) -> None:
    if has_contact_tag and result.category == "auto_archive":
        # Mail from a tagged contact is never hidden.
        result = dataclasses.replace(result, category="worth_reading")
    await apply_triage_result(email_id, result)


async def process_batch() -> int:
    emails = await list_unprocessed_emails(limit=BATCH_SIZE)
    if not emails:
        return 0

    user_ids = list({email.user_id for email in emails})
    contexts = await asyncio.gather(*(get_user(uid) for uid in user_ids))
    ctx_by_user = {user.id: user.default_context for user in contexts}

    processed = 0
    batch_cost = Decimal("0")

    for email in emails:
        if batch_cost >= Decimal(str(BATCH_COST_CAP_USD)):
            logger.warning(
                "ai_worker cost cap $%.2f reached after %d emails - stopping batch",
                BATCH_COST_CAP_USD,
                processed,
            )
            break
        try:
            result = await triage_email(email, ctx_by_user[email.user_id])
            await _apply_with_tag_override(
                email.id,
                result,
                has_contact_tag=email.contact_tag is not None,
            )
            batch_cost += result.cost_usd
            processed += 1
        except (AIInvalidResponse, AIServiceUnavailable) as exc:
            logger.warning("ai failed email_id=%s err=%s", email.id, exc)
            await mark_ai_failed(email.id)

    return processed


async def run_forever() -> None:
    while True:
        await asyncio.sleep(WORKER_INTERVAL_SECONDS)
        try:
            await process_batch()
        except Exception:
            logger.exception("ai_worker batch crashed")
