from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.email import Email

_USER_ID = uuid4()
_OTHER_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


def _make_email(user_id=_USER_ID) -> Email:
    return Email(
        id=uuid4(),
        user_id=user_id,
        account_id=uuid4(),
        gmail_id="gmail-1",
        subject="Hello",
        sender="sender@example.com",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_email_body_strips_script_tags(authed_client: TestClient) -> None:
    email = _make_email()
    html = "<article><h1>Hello</h1><script>alert('x')</script><p>Body</p></article>"
    with (
        patch("app.routers.emails.get_email", new_callable=AsyncMock, return_value=email),
        patch("app.routers.emails.fetch_email_body_html", new_callable=AsyncMock, return_value=html),
    ):
        resp = authed_client.get(f"/emails/{email.id}/body")

    assert resp.status_code == 200
    assert "<script" not in resp.json()["body_html"]
    assert "Hello" in resp.json()["body_html"]


def test_get_email_body_enforces_rls_isolation(authed_client: TestClient) -> None:
    email = _make_email(user_id=_OTHER_USER_ID)
    with patch("app.routers.emails.get_email", new_callable=AsyncMock, return_value=email):
        resp = authed_client.get(f"/emails/{email.id}/body")

    assert resp.status_code == 404
