from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.clock import utc_now
from app.core.errors import NotFoundError
from app.services.jobs import JobRegistry


def test_create_and_fetch_for_owner() -> None:
    registry = JobRegistry()
    owner = uuid4()
    job = registry.create(owner, total=5)
    assert registry.get_for_user(job.job_id, owner) is job
    assert job.status == "running"
    assert job.processed == 0


def test_other_users_cannot_see_job() -> None:
    registry = JobRegistry()
    job = registry.create(uuid4(), total=1)
    with pytest.raises(NotFoundError):
        registry.get_for_user(job.job_id, uuid4())


def test_unknown_job_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        JobRegistry().get_for_user("missing", uuid4())


def test_finished_jobs_past_ttl_are_evicted_on_create() -> None:
    registry = JobRegistry(ttl=timedelta(minutes=5))
    owner = uuid4()
    old = registry.create(owner, total=1)
    old.status = "done"
    old.created_at = utc_now() - timedelta(minutes=10)
    running = registry.create(owner, total=1)
    running.created_at = utc_now() - timedelta(minutes=10)

    registry.create(owner, total=1)

    with pytest.raises(NotFoundError):
        registry.get_for_user(old.job_id, owner)
    assert registry.get_for_user(running.job_id, owner) is running
