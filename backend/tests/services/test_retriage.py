from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.ai import TriageResponse
from app.models.email import Email


def _email(user_id) -> Email:
    return Email(
        id=uuid4(),
        user_id=user_id,
        account_id=uuid4(),
        gmail_id=uuid4().hex,
        subject="Subject",
        sender="sender@example.com",
        received_at=datetime(2026, 5, 13, tzinfo=UTC),
        body_text="Body",
        created_at=datetime(2026, 5, 13, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_start_retriage_rate_limits_second_request() -> None:
    from app.services import retriage

    retriage._last_request_at.clear()
    user_id = uuid4()
    with (
        patch("app.services.retriage.update_default_context", new=AsyncMock()),
        patch("app.services.retriage.list_emails_for_retriage", new=AsyncMock(return_value=[])),
    ):
        await retriage.start_retriage(user_id, "Daily")
        with pytest.raises(retriage.RateLimited):
            await retriage.start_retriage(user_id, "Shopping")


@pytest.mark.asyncio
async def test_start_retriage_does_not_rate_limit_different_users() -> None:
    from app.services import retriage

    retriage._last_request_at.clear()
    user1 = uuid4()
    user2 = uuid4()

    with (
        patch("app.services.retriage.update_default_context", new=AsyncMock()),
        patch("app.services.retriage.list_emails_for_retriage", new=AsyncMock(return_value=[])),
    ):
        await retriage.start_retriage(user1, "Daily")
        # user1 is now rate limited — user2 must still succeed
        job = await retriage.start_retriage(user2, "Shopping")

    assert job.user_id == user2


@pytest.mark.asyncio
async def test_retriage_job_tracking_moves_to_done() -> None:
    from app.services import retriage

    retriage._last_request_at.clear()
    user_id = uuid4()
    emails = [_email(user_id), _email(user_id)]
    triage = TriageResponse(
        category="auto_archive",
        summary="Generic notification.",
        has_deadline=False,
        has_action_items=False,
        is_pickup_code=False,
    )

    with (
        patch("app.services.retriage.update_default_context", new=AsyncMock()),
        patch("app.services.retriage.list_emails_for_retriage", new=AsyncMock(return_value=emails)),
        patch("app.services.retriage.call_json", new=AsyncMock(return_value=triage)),
        patch("app.services.retriage.update_email_triage_only", new=AsyncMock()),
    ):
        job = await retriage.start_retriage(user_id, "Daily")
        for _ in range(20):
            if job.status == "done":
                break
            await asyncio.sleep(0.01)

    assert job.status == "done"
    assert job.processed == 2
    assert job.total == 2


def test_evict_stale_entries_removes_old_jobs() -> None:
    from app.services.retriage import JOBS, RetriageJob, _evict_stale_entries, _last_request_at

    JOBS.clear()
    _last_request_at.clear()
    job_id = "old_job"
    user_id = uuid4()
    old_job = RetriageJob(job_id=job_id, user_id=user_id, total=5)
    old_job.status = "done"
    old_job.created_at = datetime.now(UTC) - timedelta(seconds=7201)
    JOBS[job_id] = old_job
    _last_request_at[user_id] = datetime.now(UTC) - timedelta(seconds=7201)

    _evict_stale_entries(ttl_seconds=3600)

    assert job_id not in JOBS
    assert user_id not in _last_request_at


def test_evict_stale_entries_keeps_recent_jobs() -> None:
    from app.services.retriage import JOBS, RetriageJob, _evict_stale_entries, _last_request_at

    JOBS.clear()
    _last_request_at.clear()
    job_id = "new_job"
    user_id = uuid4()
    JOBS[job_id] = RetriageJob(job_id=job_id, user_id=user_id, total=3)
    _last_request_at[user_id] = datetime.now(UTC)

    _evict_stale_entries(ttl_seconds=3600)

    assert job_id in JOBS
    assert user_id in _last_request_at
