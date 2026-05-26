from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.email import Email
from app.models.user import User
from app.services.openai_client import AIServiceUnavailable


def _email(subject: str, deadline: str | None = None) -> Email:
    return Email(
        id=uuid4(),
        user_id=uuid4(),
        account_id=uuid4(),
        gmail_id=uuid4().hex,
        subject=subject,
        sender="sender@example.com",
        deadline_extracted=deadline,
        received_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        created_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
    )


def _user(user_id=None) -> User:
    return User(
        id=user_id or uuid4(),
        email="user@example.com",
        default_context="Daily",
        created_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_generate_daily_digest_returns_ai_items_when_successful() -> None:
    from app.models.ai import DigestItem, DigestResponse
    from app.services.digest import generate_daily_digest

    action_email = _email("Interview follow-up required")
    item = DigestItem(
        summary="Follow up on Anthropic interview.",
        source_email_id=action_email.id,
        sender=action_email.sender or "",
    )
    response = DigestResponse(items=[item])

    with (
        patch("app.services.digest.get_user", new=AsyncMock(return_value=_user())),
        patch("app.services.digest.list_action_required_recent", new=AsyncMock(return_value=[action_email])),
        patch("app.services.digest.list_upcoming_deadlines", new=AsyncMock(return_value=[])),
        patch("app.services.digest.call_json", new=AsyncMock(return_value=response)),
    ):
        digest = await generate_daily_digest(uuid4())

    assert digest.degraded is False
    assert len(digest.items) == 1
    assert digest.items[0].summary == "Follow up on Anthropic interview."


@pytest.mark.asyncio
async def test_generate_daily_digest_returns_empty_when_no_emails() -> None:
    from app.services.digest import generate_daily_digest

    call_json = AsyncMock()
    with (
        patch("app.services.digest.get_user", new=AsyncMock(return_value=_user())),
        patch("app.services.digest.list_action_required_recent", new=AsyncMock(return_value=[])),
        patch("app.services.digest.list_upcoming_deadlines", new=AsyncMock(return_value=[])),
        patch("app.services.digest.call_json", call_json),
    ):
        digest = await generate_daily_digest(uuid4())

    assert digest.items == []
    assert digest.degraded is False
    call_json.assert_not_awaited()


@pytest.mark.asyncio
async def test_digest_degraded_fallback_includes_upcoming_deadlines() -> None:
    from app.services.digest import generate_daily_digest

    deadline_email = _email("Tuition deposit due", "2026-05-18")
    with (
        patch("app.services.digest.get_user", new=AsyncMock(return_value=_user())),
        patch("app.services.digest.list_action_required_recent", new=AsyncMock(return_value=[])),
        patch("app.services.digest.list_upcoming_deadlines", new=AsyncMock(return_value=[deadline_email])),
        patch("app.services.digest.call_json", new=AsyncMock(side_effect=AIServiceUnavailable("down"))),
    ):
        digest = await generate_daily_digest(uuid4())

    assert digest.degraded is True
    assert len(digest.items) == 1
    assert digest.items[0].summary == "Tuition deposit due"
    assert digest.items[0].deadline.isoformat() == "2026-05-18"
