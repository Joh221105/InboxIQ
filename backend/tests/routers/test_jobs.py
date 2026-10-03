from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.core.errors import RateLimitedError
from app.main import app
from app.models.user import User
from app.services.retriage import RETRIAGE_JOBS

_USER_ID = UUID("12345678-1234-5678-1234-567812345678")


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    RETRIAGE_JOBS.clear()


def test_patch_users_me_context_starts_retriage(authed_client: TestClient) -> None:
    user = User(
        id=_USER_ID,
        email="user@example.com",
        default_context="Shopping",
        created_at=datetime.now(UTC),
    )
    job = RETRIAGE_JOBS.create(_USER_ID, total=7)

    with (
        patch("app.routers.users.get_user", new=AsyncMock(return_value=user)),
        patch("app.routers.users.start_retriage", new=AsyncMock(return_value=job)),
    ):
        resp = authed_client.patch("/users/me/context", json={"context": "Shopping"})

    assert resp.status_code == 200
    assert resp.json()["job_id"] == job.job_id
    assert resp.json()["total"] == 7
    assert resp.json()["user"]["default_context"] == "Shopping"


def test_patch_users_me_context_rate_limited(authed_client: TestClient) -> None:
    with patch("app.routers.users.start_retriage", new=AsyncMock(side_effect=RateLimitedError(42))):
        resp = authed_client.patch("/users/me/context", json={"context": "Daily"})

    assert resp.status_code == 429
    assert resp.headers["retry-after"] == "42"
    assert resp.json() == {
        "detail": {
            "code": "rate_limited",
            "message": "Too many requests. Try again shortly.",
            "retry_after_seconds": 42,
        }
    }


def test_get_job_for_owner_returns_status(authed_client: TestClient) -> None:
    job = RETRIAGE_JOBS.create(_USER_ID, total=3)
    job.processed = 2

    resp = authed_client.get(f"/jobs/{job.job_id}")

    assert resp.status_code == 200
    assert resp.json() == {"job_id": job.job_id, "status": "running", "processed": 2, "total": 3}


def test_get_job_for_other_user_returns_404(authed_client: TestClient) -> None:
    job = RETRIAGE_JOBS.create(uuid4(), total=3)

    resp = authed_client.get(f"/jobs/{job.job_id}")

    assert resp.status_code == 404
