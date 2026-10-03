from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.connected_account import ConnectedAccount, OAuthTokens

_USER_ID = uuid4()
_EMAIL = "owner@example.com"


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email=_EMAIL)


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


def _make_account(user_id: UUID, account_id: UUID | None = None) -> ConnectedAccount:
    return ConnectedAccount(
        id=account_id or uuid4(),
        user_id=user_id,
        email_address="work@gmail.com",
        provider="gmail",
        color="#4F46E5",
        last_synced=None,
        disconnected_at=None,
        disconnected_reason=None,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        oauth_token=OAuthTokens(
            access_token="acc_tok",
            refresh_token="ref_tok",
            expires_at=datetime(2026, 1, 1, tzinfo=UTC),
            scope="https://www.googleapis.com/auth/gmail.modify",
        ),
    )


# --- GET /accounts ---


def test_list_accounts_returns_own_only(authed_client: TestClient) -> None:
    acct = _make_account(_USER_ID)
    with patch(
        "app.routers.accounts.list_user_accounts", new_callable=AsyncMock, return_value=[acct]
    ):
        resp = authed_client.get("/accounts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["email_address"] == "work@gmail.com"


def test_list_accounts_no_oauth_token_in_response(authed_client: TestClient) -> None:
    acct = _make_account(_USER_ID)
    with patch(
        "app.routers.accounts.list_user_accounts", new_callable=AsyncMock, return_value=[acct]
    ):
        resp = authed_client.get("/accounts")
    assert resp.status_code == 200
    for item in resp.json():
        assert "oauth_token" not in item
        assert "access_token" not in item
        assert "refresh_token" not in item


def test_list_accounts_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.get("/accounts")
    assert resp.status_code == 401


# --- DELETE /accounts/{id} ---


def test_delete_account_as_owner(authed_client: TestClient) -> None:
    account_id = uuid4()
    acct = _make_account(_USER_ID, account_id)
    with (
        patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=acct),
        patch("app.routers.accounts.revoke", new_callable=AsyncMock) as mock_revoke,
        patch("app.routers.accounts.delete_account", new_callable=AsyncMock),
    ):
        resp = authed_client.delete(f"/accounts/{account_id}")
    assert resp.status_code == 204
    mock_revoke.assert_awaited_once_with("ref_tok")


def test_delete_account_wrong_user_returns_404(authed_client: TestClient) -> None:
    account_id = uuid4()
    other_user_id = uuid4()
    acct = _make_account(other_user_id, account_id)  # belongs to someone else
    with patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=acct):
        resp = authed_client.delete(f"/accounts/{account_id}")
    assert resp.status_code == 404


def test_delete_account_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.delete(f"/accounts/{uuid4()}")
    assert resp.status_code == 401
