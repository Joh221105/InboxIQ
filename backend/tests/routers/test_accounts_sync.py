# backend/tests/routers/test_accounts_sync.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.connected_account import ConnectedAccount, OAuthTokens
from app.models.email import SyncResult

_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


def _make_account(disconnected_at=None) -> ConnectedAccount:
    return ConnectedAccount(
        id=uuid4(),
        user_id=_USER_ID,
        provider="gmail",
        email_address="work@gmail.com",
        oauth_token=OAuthTokens(
            access_token="acc",
            refresh_token="ref",
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            scope="https://www.googleapis.com/auth/gmail.readonly",
        ),
        color="#4F46E5",
        disconnected_at=disconnected_at,
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


def test_sync_account_returns_sync_result(authed_client: TestClient) -> None:
    account = _make_account()
    sync_result = SyncResult(fetched=5, inserted=5, updated=0, errors=0)

    with (
        patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.routers.accounts.sync_account", new_callable=AsyncMock, return_value=sync_result),
    ):
        resp = authed_client.post(f"/accounts/{account.id}/sync")

    assert resp.status_code == 200
    data = resp.json()
    assert data["fetched"] == 5
    assert data["inserted"] == 5


def test_sync_wrong_user_returns_404(authed_client: TestClient) -> None:
    account = _make_account()
    account = account.model_copy(update={"user_id": uuid4()})  # different user

    with patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=account):
        resp = authed_client.post(f"/accounts/{account.id}/sync")

    assert resp.status_code == 404


def test_sync_disconnected_account_returns_409(authed_client: TestClient) -> None:
    account = _make_account(disconnected_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

    with patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=account):
        resp = authed_client.post(f"/accounts/{account.id}/sync")

    assert resp.status_code == 409
    assert resp.json()["reason"] == "disconnected"


def test_sync_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.post(f"/accounts/{uuid4()}/sync")
    assert resp.status_code == 401
