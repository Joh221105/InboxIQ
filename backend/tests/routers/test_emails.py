# backend/tests/routers/test_emails.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.email import Email, EmailListPage

_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


def _make_email(user_id=None) -> Email:
    return Email(
        id=uuid4(),
        user_id=user_id or _USER_ID,
        account_id=uuid4(),
        gmail_id="msg1",
        subject="Hello",
        sender="alice@example.com",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        is_read=False,
        labels=[],
        is_archived=False,
        account_color="#4F46E5",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client() -> TestClient:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_list_emails_returns_200_with_items(authed_client: TestClient) -> None:
    page = EmailListPage(items=[_make_email()], next_cursor=None)
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page):
        resp = authed_client.get("/emails")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["next_cursor"] is None


def test_list_emails_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.get("/emails")
    assert resp.status_code == 401


def test_list_emails_no_oauth_token_in_response(authed_client: TestClient) -> None:
    page = EmailListPage(items=[_make_email()], next_cursor=None)
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page):
        resp = authed_client.get("/emails")
    for item in resp.json()["items"]:
        assert "oauth_token" not in item
        assert "access_token" not in item
        assert "refresh_token" not in item


def test_list_emails_rls_isolation(authed_client: TestClient) -> None:
    other_user_email = _make_email(user_id=uuid4())
    page = EmailListPage(items=[other_user_email], next_cursor=None)
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page) as mock_list:
        resp = authed_client.get("/emails")
    # The router must pass the current user's ID to list_emails, not trust the request
    call_filters = mock_list.call_args[0][0]
    assert call_filters.user_id == _USER_ID


def test_list_emails_with_cursor(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor="abc123")
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page):
        resp = authed_client.get("/emails?cursor=some_cursor&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["next_cursor"] == "abc123"
