from __future__ import annotations

from datetime import date
from uuid import UUID

from app.core.clock import utc_now, utc_today
from app.db.emails import (
    get_digest,
    list_action_required_recent,
    list_upcoming_deadlines,
    upsert_digest,
)
from app.db.users import get_user
from app.models.ai import Digest, DigestItem, DigestResponse
from app.models.email import Email
from app.prompts.digest import DIGEST_PROMPT
from app.services.openai_client import AIInvalidResponse, AIServiceUnavailable, call_json


def _deadline_value(email: Email) -> str:
    return email.deadline_extracted or ""


def _digest_item_from_email(email: Email) -> DigestItem:
    summary = (email.ai_summary or email.subject or "")[:80]
    return DigestItem(
        summary=summary,
        source_email_id=email.id,
        deadline=date.fromisoformat(email.deadline_extracted) if email.deadline_extracted else None,
        sender=email.sender or "",
    )


def format_digest_input(actions: list[Email], deadlines: list[Email]) -> str:
    lines = ["Action-required emails from the last 24 hours:"]
    for email in actions:
        lines.append(
            f"- id={email.id}; sender={email.sender or ''}; subject={email.subject or ''}; "
            f"summary={email.ai_summary or ''}; deadline={_deadline_value(email)}"
        )
    lines.append("Upcoming deadlines in the next 7 days:")
    for email in deadlines:
        lines.append(
            f"- id={email.id}; sender={email.sender or ''}; subject={email.subject or ''}; "
            f"summary={email.ai_summary or ''}; deadline={_deadline_value(email)}"
        )
    return "\n".join(lines)


async def generate_daily_digest(user_id: UUID) -> Digest:
    user = await get_user(user_id)
    actions = await list_action_required_recent(user_id, hours=24)
    deadlines = await list_upcoming_deadlines(user_id, days=7)

    if not actions and not deadlines:
        return Digest(items=[], degraded=False, context=user.default_context)

    user_msg = format_digest_input(actions, deadlines)
    try:
        resp = await call_json(
            system=DIGEST_PROMPT,
            user=user_msg,
            response_model=DigestResponse,
            kind="digest",
            user_id=user_id,
        )
        return Digest(items=resp.items, degraded=False, context=user.default_context)
    except (AIInvalidResponse, AIServiceUnavailable):
        fallback_source = (actions + [email for email in deadlines if email not in actions])[:3]
        fallback = [_digest_item_from_email(email) for email in fallback_source]
        return Digest(items=fallback, degraded=True, context=user.default_context)


async def get_or_create_today_digest(user_id: UUID) -> Digest:
    today = utc_today()
    cached = await get_digest(user_id, today)
    if cached and (utc_now() - cached.generated_at).total_seconds() < 3600:
        user = await get_user(user_id)
        return cached.payload.model_copy(
            update={"generated_at": cached.generated_at, "context": user.default_context}
        )
    digest = await generate_daily_digest(user_id)
    await upsert_digest(user_id, today, digest)
    return digest
