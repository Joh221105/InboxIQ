from __future__ import annotations

import asyncio
import logging

from app.db.emails import apply_triage_result, list_unprocessed_emails, mark_ai_failed
from app.db.users import get_user
from app.services.openai_client import AIInvalidResponse, AIServiceUnavailable
from app.services.triage import triage_email

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
BATCH_COST_CAP_USD = 0.50
WORKER_INTERVAL_SECONDS = 30


async def process_batch() -> int:
    emails = await list_unprocessed_emails(limit=BATCH_SIZE)
    if not emails:
        return 0

    user_ids = list({email.user_id for email in emails})
    contexts = await asyncio.gather(*(get_user(uid) for uid in user_ids))
    ctx_by_user = {user.id: user.default_context for user in contexts}

    async def process_one(email) -> str:
        try:
            result = await triage_email(email, ctx_by_user[email.user_id])
            await apply_triage_result(email.id, result)
            return "ok"
        except (AIInvalidResponse, AIServiceUnavailable) as exc:
            logger.warning("ai failed email_id=%s err=%s", email.id, exc)
            await mark_ai_failed(email.id)
            return "failed"

    results = await asyncio.gather(*(process_one(email) for email in emails))
    return sum(1 for result in results if result == "ok")


async def run_forever() -> None:
    while True:
        await asyncio.sleep(WORKER_INTERVAL_SECONDS)
        try:
            await process_batch()
        except Exception:
            logger.exception("ai_worker batch crashed")
