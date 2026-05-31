from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.ai import Digest, DigestItem

_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


def _make_digest(**kwargs) -> Digest:
    defaults: dict = dict(
        generated_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        items=[
            DigestItem(
                summary="Pick up your package at locker A3",
                source_email_id=uuid4(),
                deadline=None,
                sender="shipping@example.com",
            )
        ],
        degraded=False,
        context="Daily",
    )
    defaults.update(kwargs)
    return Digest(**defaults)


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client() -> TestClient:
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c


def test_get_today_digest_success(authed_client: TestClient) -> None:
    digest = _make_digest()
    with patch(
        "app.routers.digest.get_or_create_today_digest",
        new_callable=AsyncMock,
        return_value=digest,
    ):
        resp = authed_client.get("/digest/today")

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "degraded" in body
    assert "context" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 1
    assert body["degraded"] is False
    assert body["context"] == "Daily"


def test_get_today_digest_unauthenticated(unauthed_client: TestClient) -> None:
    resp = unauthed_client.get("/digest/today")
    assert resp.status_code in (401, 403)


def test_get_today_digest_empty(authed_client: TestClient) -> None:
    digest = _make_digest(items=[])
    with patch(
        "app.routers.digest.get_or_create_today_digest",
        new_callable=AsyncMock,
        return_value=digest,
    ):
        resp = authed_client.get("/digest/today")

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []


def test_get_today_digest_degraded(authed_client: TestClient) -> None:
    digest = _make_digest(degraded=True)
    with patch(
        "app.routers.digest.get_or_create_today_digest",
        new_callable=AsyncMock,
        return_value=digest,
    ):
        resp = authed_client.get("/digest/today")

    assert resp.status_code == 200
    body = resp.json()
    assert body["degraded"] is True
