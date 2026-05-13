from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.ai import ActionItemsResponse, DeadlineResponse, PickupCodeResponse, TriageResponse
from app.models.email import Email


def _email(subject: str = "Interview", body: str = "Please complete by Friday") -> Email:
    return Email(
        id=uuid4(),
        user_id=uuid4(),
        account_id=uuid4(),
        gmail_id="gmail-1",
        subject=subject,
        sender="recruiter@example.com",
        received_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        body_text=body,
        created_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_triage_email_empty_body_skips_openai() -> None:
    from app.services.triage import triage_email

    call_json = AsyncMock()
    with patch("app.services.triage.call_json", call_json):
        result = await triage_email(_email(body="   "), "Job Hunting")

    assert result.category == "auto_archive"
    assert result.summary == "(No readable content)"
    assert result.triage_context == "Job Hunting"
    call_json.assert_not_awaited()


@pytest.mark.asyncio
async def test_triage_email_extracts_deadline_when_flagged() -> None:
    from app.services.triage import triage_email

    call_json = AsyncMock(
        side_effect=[
            TriageResponse(
                category="action_required",
                summary="Recruiter asks you to complete an OA by Friday.",
                has_deadline=True,
                has_action_items=False,
                is_pickup_code=False,
            ),
            DeadlineResponse(deadline="2026-05-15", deadline_text="by Friday", confidence="high"),
        ]
    )

    with patch("app.services.triage.call_json", call_json):
        result = await triage_email(_email(), "Job Hunting")

    assert call_json.await_count == 2
    assert result.deadline_extracted.isoformat() == "2026-05-15"


@pytest.mark.asyncio
async def test_triage_email_pickup_prefilter_runs_pickup_extraction() -> None:
    from app.services.triage import triage_email

    call_json = AsyncMock(
        side_effect=[
            TriageResponse(
                category="worth_reading",
                summary="Amazon says your package is ready.",
                has_deadline=False,
                has_action_items=False,
                is_pickup_code=False,
            ),
            PickupCodeResponse(
                pickup_code="1234 5678",
                pickup_expiry="2026-05-15",
                retailer="Amazon",
                locker_location="Campus Hub",
            ),
        ]
    )

    with patch("app.services.triage.call_json", call_json):
        result = await triage_email(
            _email(subject="Your Amazon Locker pickup code is 1234 5678", body="Ready for pickup"),
            "Shopping",
        )

    assert call_json.await_count == 2
    assert result.is_pickup_code is True
    assert result.pickup_code == "1234 5678"


@pytest.mark.asyncio
async def test_triage_email_does_not_persist_pickup_flag_without_code() -> None:
    from app.services.triage import triage_email

    call_json = AsyncMock(
        side_effect=[
            TriageResponse(
                category="action_required",
                summary="Package is ready for pickup.",
                has_deadline=False,
                has_action_items=True,
                is_pickup_code=True,
            ),
            ActionItemsResponse(action_items=["Pick up package"]),
            PickupCodeResponse(),
        ]
    )

    with patch("app.services.triage.call_json", call_json):
        result = await triage_email(
            _email(subject="Ready for pickup", body="Your package is ready but no code is shown."),
            "Shopping",
        )

    assert result.is_pickup_code is False
    assert result.pickup_code is None


@pytest.mark.asyncio
async def test_triage_email_extracts_action_items_when_flagged() -> None:
    from app.services.triage import triage_email

    call_json = AsyncMock(
        side_effect=[
            TriageResponse(
                category="action_required",
                summary="School requests your transcript.",
                has_deadline=False,
                has_action_items=True,
                is_pickup_code=False,
            ),
            ActionItemsResponse(action_items=["Upload transcript"]),
        ]
    )

    with patch("app.services.triage.call_json", call_json):
        result = await triage_email(_email(body="Please upload your transcript."), "School Application")

    assert call_json.await_count == 2
    assert result.action_items == ["Upload transcript"]
