from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.user import User

_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
_EMAIL = "test@example.com"
_USER = User(
    id=_USER_ID,
    email=_EMAIL,
    default_context="Daily",
    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
)


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email=_EMAIL)


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client() -> TestClient:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- GET /users/me ---


def test_get_me_happy(authed_client: TestClient) -> None:
    with patch("app.routers.users.get_user", new=AsyncMock(return_value=_USER)):
        resp = authed_client.get("/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == _EMAIL
    assert data["default_context"] == "Daily"


def test_get_me_no_token(unauthed_client: TestClient) -> None:
    resp = unauthed_client.get("/users/me")
    assert resp.status_code == 401


def test_get_me_mangled_token(unauthed_client: TestClient) -> None:
    resp = unauthed_client.get(
        "/users/me", headers={"Authorization": "Bearer not.a.real.token"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "auth_invalid"


# --- PATCH /users/me/context ---


def test_patch_context_happy(authed_client: TestClient) -> None:
    updated = _USER.model_copy(update={"default_context": "Job Hunting"})
    job = type("Job", (), {"job_id": "job1", "total": 3})()
    with patch(
        "app.routers.users.start_retriage",
        new=AsyncMock(return_value=job),
    ), patch(
        "app.routers.users.get_user",
        new=AsyncMock(return_value=updated),
    ):
        resp = authed_client.patch(
            "/users/me/context", json={"context": "Job Hunting"}
        )
    assert resp.status_code == 200
    assert resp.json()["user"]["default_context"] == "Job Hunting"
    assert resp.json()["job_id"] == "job1"
    assert resp.json()["total"] == 3


def test_patch_context_invalid_value(authed_client: TestClient) -> None:
    resp = authed_client.patch(
        "/users/me/context", json={"context": "Invalid Context"}
    )
    assert resp.status_code == 422


def test_patch_context_no_token(unauthed_client: TestClient) -> None:
    resp = unauthed_client.patch(
        "/users/me/context", json={"context": "Daily"}
    )
    assert resp.status_code == 401


def test_get_me_not_found(authed_client: TestClient) -> None:
    with patch(
        "app.routers.users.get_user",
        new=AsyncMock(side_effect=HTTPException(status_code=404, detail="not found")),
    ):
        resp = authed_client.get("/users/me")
    assert resp.status_code == 404
