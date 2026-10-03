from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable
from decimal import Decimal
from typing import Any

from app.models.ai import (
    ActionItemsResponse,
    DeadlineResponse,
    PickupCodeResponse,
    TriageResponse,
    TriageResult,
)
from app.models.email import Email
from app.models.user import ContextMode
from app.prompts.extract import ACTION_ITEMS_PROMPT, DEADLINE_PROMPT, PICKUP_CODE_PROMPT
from app.prompts.triage import TRIAGE_PROMPTS
from app.services.ai_client import call_json_with_cost

logger = logging.getLogger(__name__)

PICKUP_PATTERNS = [
    re.compile(r"\bpickup\s+code\b", re.I),
    re.compile(r"\bready\s+for\s+pickup\b", re.I),
    re.compile(r"\bamazon\s+(hub|locker)\b", re.I),
    re.compile(r"\bfedex\s+(hold|pickup)\b", re.I),
    re.compile(r"\bups\s+access\s+point\b", re.I),
    re.compile(r"\busps\s+held\b", re.I),
    re.compile(r"\bdhl\s+(servicepoint|pickup)\b", re.I),
    re.compile(r"c[oó]digo\s+de\s+recogida", re.I),
]


def triage_message(email: Email) -> str:
    """User-turn content for triage prompts; email data never enters the system prompt."""
    return (
        f"From: {email.sender or ''}\n"
        f"Subject: {email.subject or ''}\n"
        f"Body: {(email.body_text or '')[:4000]}"
    )


def pickup_code_prefilter(email: Email) -> bool:
    text = f"{email.subject or ''} {(email.body_text or '')[:500]}"
    return any(p.search(text) for p in PICKUP_PATTERNS)


async def triage_email(email: Email, user_context: ContextMode) -> TriageResult:
    body = email.body_text or ""
    if not body.strip():
        return TriageResult(
            category="auto_archive",
            summary="Image-only email — no readable text.",
            triage_context=user_context,
        )

    triage, triage_cost = await call_json_with_cost(
        system=TRIAGE_PROMPTS[user_context],
        user=triage_message(email),
        response_model=TriageResponse,
        kind="triage",
        user_id=email.user_id,
        email_id=email.id,
    )

    result = TriageResult(
        category=triage.category,
        summary=triage.summary,
        triage_context=user_context,
        cost_usd=triage_cost,
    )

    tasks: list[tuple[str, Awaitable[tuple[Any, Decimal]]]] = []
    if triage.has_deadline:
        received_at = email.received_at.isoformat() if email.received_at else ""
        tasks.append(
            (
                "deadline",
                call_json_with_cost(
                    system=DEADLINE_PROMPT,
                    user=f"received_at: {received_at}\n\n{body}",
                    response_model=DeadlineResponse,
                    kind="deadline",
                    user_id=email.user_id,
                    email_id=email.id,
                ),
            )
        )
    if triage.has_action_items:
        tasks.append(
            (
                "actions",
                call_json_with_cost(
                    system=ACTION_ITEMS_PROMPT,
                    user=body,
                    response_model=ActionItemsResponse,
                    kind="action_items",
                    user_id=email.user_id,
                    email_id=email.id,
                ),
            )
        )
    if triage.is_pickup_code or pickup_code_prefilter(email):
        tasks.append(
            (
                "pickup",
                call_json_with_cost(
                    system=PICKUP_CODE_PROMPT,
                    user=f"Subject: {email.subject or ''}\nBody: {body}",
                    response_model=PickupCodeResponse,
                    kind="pickup",
                    user_id=email.user_id,
                    email_id=email.id,
                ),
            )
        )

    if tasks:
        outcomes = await asyncio.gather(*(task for _, task in tasks))
        for (kind, _), outcome in zip(tasks, outcomes, strict=True):
            parsed, step_cost = outcome
            result.cost_usd += step_cost
            if kind == "deadline":
                result.deadline_extracted = parsed.deadline
            elif kind == "actions":
                result.action_items = parsed.action_items
            elif kind == "pickup" and parsed.pickup_code:
                result.is_pickup_code = True
                result.pickup_code = parsed.pickup_code
                result.pickup_expiry = parsed.pickup_expiry
                result.retailer = parsed.retailer
                result.locker_location = parsed.locker_location

    return result
