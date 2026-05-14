from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date

from app.models.ai import ActionItemsResponse, DeadlineResponse, PickupCodeResponse, TriageResponse
from app.models.email import Email
from app.prompts.extract import ACTION_ITEMS_PROMPT, DEADLINE_PROMPT, PICKUP_CODE_PROMPT
from app.prompts.triage import TRIAGE_PROMPTS
from app.services.openai_client import call_json

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


def _email_body(email: Email) -> str:
    return email.body_text or ""


def _email_sender(email: Email) -> str:
    return email.sender or ""


def pickup_code_prefilter(email: Email) -> bool:
    text = f"{email.subject or ''} {_email_body(email)[:500]}"
    return any(p.search(text) for p in PICKUP_PATTERNS)


@dataclass
class TriageResult:
    category: str
    summary: str
    triage_context: str
    deadline_extracted: date | None = None
    action_items: list[str] | None = None
    is_pickup_code: bool = False
    pickup_code: str | None = None
    pickup_expiry: date | None = None
    retailer: str | None = None
    locker_location: str | None = None


async def triage_email(email: Email, user_context: str) -> TriageResult:
    body = _email_body(email)
    if not body.strip():
        return TriageResult(
            category="auto_archive",
            summary="Image-only email — no readable text.",
            triage_context=user_context,
        )

    user_msg = (
        f"From: {_email_sender(email)}\n"
        f"Subject: {email.subject or ''}\n"
        f"Body: {body[:4000]}"
    )
    triage = await call_json(
        system=TRIAGE_PROMPTS[user_context],
        user=user_msg,
        response_model=TriageResponse,
        kind="triage",
        user_id=email.user_id,
        email_id=email.id,
    )

    result = TriageResult(
        category=triage.category,
        summary=triage.summary,
        triage_context=user_context,
    )

    tasks = []
    if triage.has_deadline:
        received_at = email.received_at.isoformat() if email.received_at else ""
        tasks.append(
            (
                "deadline",
                call_json(
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
                call_json(
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
                call_json(
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
        outcomes = await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
        for (kind, _), outcome in zip(tasks, outcomes):
            if isinstance(outcome, Exception):
                logger.warning("extraction failed kind=%s err=%s", kind, outcome)
                continue
            if kind == "deadline":
                result.deadline_extracted = outcome.deadline
            elif kind == "actions":
                result.action_items = outcome.action_items
            elif kind == "pickup" and outcome.pickup_code:
                result.is_pickup_code = True
                result.pickup_code = outcome.pickup_code
                result.pickup_expiry = outcome.pickup_expiry
                result.retailer = outcome.retailer
                result.locker_location = outcome.locker_location

    return result
