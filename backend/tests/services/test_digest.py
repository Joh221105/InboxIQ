from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.email import Email
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


@pytest.mark.asyncio
async def test_digest_degraded_fallback_includes_upcoming_deadlines() -> None:
    from app.services.digest import generate_daily_digest

    deadline_email = _email("Tuition deposit due", "2026-05-18")
    with (
        patch("app.services.digest.list_action_required_recent", new=AsyncMock(return_value=[])),
        patch("app.services.digest.list_upcoming_deadlines", new=AsyncMock(return_value=[deadline_email])),
        patch("app.services.digest.call_json", new=AsyncMock(side_effect=AIServiceUnavailable("down"))),
    ):
        digest = await generate_daily_digest(uuid4())

    assert digest.degraded is True
    assert len(digest.items) == 1
    assert digest.items[0].summary == "Tuition deposit due"
    assert digest.items[0].deadline.isoformat() == "2026-05-18"
