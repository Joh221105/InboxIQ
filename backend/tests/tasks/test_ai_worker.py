from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.email import Email
from app.models.user import User
from app.services.openai_client import AIServiceUnavailable
from app.services.triage import TriageResult


def _email(user_id=None) -> Email:
    return Email(
        id=uuid4(),
        user_id=user_id or uuid4(),
        account_id=uuid4(),
        gmail_id=uuid4().hex,
        subject="Subject",
        sender="sender@example.com",
        received_at=datetime(2026, 5, 13, tzinfo=UTC),
        body_text="Body",
        created_at=datetime(2026, 5, 13, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_process_batch_returns_zero_when_no_emails() -> None:
    from app.tasks.ai_worker import process_batch

    triage_email = AsyncMock()
    with patch("app.tasks.ai_worker.list_unprocessed_emails", new=AsyncMock(return_value=[])):
        count = await process_batch()

    assert count == 0
    triage_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_batch_applies_success_and_marks_failure() -> None:
    from app.tasks.ai_worker import process_batch

    user_id = uuid4()
    emails = [_email(user_id), _email(user_id)]
    user = User(
        id=user_id, email="u@example.com", default_context="Daily", created_at=datetime.now(UTC)
    )
    result = TriageResult(category="worth_reading", summary="Summary", triage_context="Daily")

    with (
        patch("app.tasks.ai_worker.list_unprocessed_emails", new=AsyncMock(return_value=emails)),
        patch("app.tasks.ai_worker.get_user", new=AsyncMock(return_value=user)),
        patch(
            "app.tasks.ai_worker.triage_email",
            new=AsyncMock(side_effect=[result, AIServiceUnavailable("down")]),
        ),
        patch("app.tasks.ai_worker.apply_triage_result", new=AsyncMock()) as apply_result,
        patch("app.tasks.ai_worker.mark_ai_failed", new=AsyncMock()) as mark_failed,
    ):
        count = await process_batch()

    assert count == 1
    apply_result.assert_awaited_once_with(emails[0].id, result)
    mark_failed.assert_awaited_once_with(emails[1].id)


@pytest.mark.asyncio
async def test_process_batch_stops_when_cost_cap_exceeded() -> None:
    from app.tasks.ai_worker import process_batch

    user_id = uuid4()
    emails = [_email(user_id) for _ in range(5)]
    user = User(
        id=user_id, email="u@example.com", default_context="Daily", created_at=datetime.now(UTC)
    )

    async def _fake_triage(_email: Email, _context: str) -> TriageResult:
        return TriageResult(
            category="auto_archive",
            summary="test",
            triage_context="Daily",
            cost_usd=Decimal("0.30"),
        )

    with (
        patch("app.tasks.ai_worker.list_unprocessed_emails", new=AsyncMock(return_value=emails)),
        patch("app.tasks.ai_worker.get_user", new=AsyncMock(return_value=user)),
        patch("app.tasks.ai_worker.triage_email", side_effect=_fake_triage),
        patch("app.tasks.ai_worker.apply_triage_result", new=AsyncMock()) as apply_result,
    ):
        count = await process_batch()

    assert count == 2
    assert apply_result.await_count == 2


@pytest.mark.asyncio
async def test_tagged_contact_email_upgraded_from_auto_archive() -> None:
    from app.tasks.ai_worker import _apply_with_tag_override

    email_id = uuid4()
    result = TriageResult(category="auto_archive", summary="Newsletter", triage_context="Daily")
    applied: dict[str, str] = {}

    async def _fake_apply(_email_id, triage_result):
        applied["category"] = triage_result.category

    with patch("app.tasks.ai_worker.apply_triage_result", side_effect=_fake_apply):
        await _apply_with_tag_override(email_id, result, has_contact_tag=True)

    assert applied["category"] == "worth_reading"


@pytest.mark.asyncio
async def test_tagged_contact_email_does_not_downgrade_action_required() -> None:
    from app.tasks.ai_worker import _apply_with_tag_override

    email_id = uuid4()
    result = TriageResult(category="action_required", summary="Interview", triage_context="Daily")
    applied: dict[str, str] = {}

    async def _fake_apply(_email_id, triage_result):
        applied["category"] = triage_result.category

    with patch("app.tasks.ai_worker.apply_triage_result", side_effect=_fake_apply):
        await _apply_with_tag_override(email_id, result, has_contact_tag=True)

    assert applied["category"] == "action_required"


@pytest.mark.asyncio
async def test_untagged_email_auto_archive_not_changed() -> None:
    from app.tasks.ai_worker import _apply_with_tag_override

    email_id = uuid4()
    result = TriageResult(category="auto_archive", summary="Newsletter", triage_context="Daily")
    applied: dict[str, str] = {}

    async def _fake_apply(_email_id, triage_result):
        applied["category"] = triage_result.category

    with patch("app.tasks.ai_worker.apply_triage_result", side_effect=_fake_apply):
        await _apply_with_tag_override(email_id, result, has_contact_tag=False)

    assert applied["category"] == "auto_archive"
