from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.email import Email, EmailCounts, EmailListPage

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
        received_at=datetime(2025, 6, 1, tzinfo=UTC),
        is_read=False,
        labels=[],
        is_archived=False,
        account_color="#4F46E5",
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
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
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        authed_client.get("/emails")
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


def test_list_emails_passes_search_param(authed_client: TestClient) -> None:
    page = EmailListPage(items=[_make_email()], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get("/emails?search=amazon")

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.search == "amazon"


def test_list_emails_passes_sender_search_param(authed_client: TestClient) -> None:
    page = EmailListPage(items=[_make_email()], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get("/emails?sender_search=alice")

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.sender_search == "alice"


def test_list_emails_passes_contact_tag_id_param(authed_client: TestClient) -> None:
    contact_tag_id = uuid4()
    page = EmailListPage(items=[], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get(f"/emails?contact_tag_id={contact_tag_id}")

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.contact_tag_id == contact_tag_id


def test_list_emails_blank_sender_search_is_ignored(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get("/emails?sender_search=")

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.sender_search is None


def test_list_emails_special_char_search_does_not_crash(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get("/emails", params={"search": "')(*&"})

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.search == "')(*&"


def test_list_emails_all_tab_uses_priority_order_flag(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get("/emails")

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.triage_category is None


def test_list_emails_passes_deadline_filters(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get(
            "/emails?has_deadline=true&deadline_after=2026-05-14&deadline_before=2026-05-21"
        )

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.has_deadline is True
    assert call_filters.deadline_after.isoformat() == "2026-05-14"
    assert call_filters.deadline_before.isoformat() == "2026-05-21"


def test_list_emails_passes_deadline_ascending_order(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor=None)
    with patch(
        "app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page
    ) as mock_list:
        resp = authed_client.get("/emails?order=deadline_asc")

    assert resp.status_code == 200
    call_filters = mock_list.call_args[0][0]
    assert call_filters.order == "deadline_asc"


def test_email_counts_returns_counts(authed_client: TestClient) -> None:
    counts = EmailCounts(all=4, action_required=1, worth_reading=2, auto_archive=1)
    with patch(
        "app.routers.emails.get_email_counts", new_callable=AsyncMock, return_value=counts
    ) as mock_counts:
        resp = authed_client.get("/emails/counts")

    assert resp.status_code == 200
    assert resp.json() == {
        "all": 4,
        "action_required": 1,
        "worth_reading": 2,
        "auto_archive": 1,
    }
    mock_counts.assert_awaited_once_with(_USER_ID)


def test_patch_email_returns_updated_email(authed_client: TestClient) -> None:
    email = _make_email()
    with patch(
        "app.routers.emails.update_email", new_callable=AsyncMock, return_value=email
    ) as mock_update:
        resp = authed_client.patch(f"/emails/{email.id}", json={"is_archived": True})

    assert resp.status_code == 200
    assert resp.json()["id"] == str(email.id)
    mock_update.assert_awaited_once()


def test_patch_email_passes_is_read_to_update(authed_client: TestClient) -> None:
    email = _make_email().model_copy(update={"is_read": True})
    with patch(
        "app.routers.emails.update_email", new_callable=AsyncMock, return_value=email
    ) as mock_update:
        resp = authed_client.patch(f"/emails/{email.id}", json={"is_read": True})

    assert resp.status_code == 200
    patch_body = mock_update.call_args[0][2]
    assert patch_body.is_read is True


def test_patch_email_archives_gmail_when_pickup_marked_used(authed_client: TestClient) -> None:
    email = _make_email()
    updated = email.model_copy(update={"pickup_used": True, "is_archived": True})
    with (
        patch(
            "app.routers.emails.get_email", new_callable=AsyncMock, return_value=email
        ) as mock_get,
        patch("app.routers.emails.archive_gmail_message", new_callable=AsyncMock) as mock_archive,
        patch("app.routers.emails.update_email", new_callable=AsyncMock, return_value=updated),
    ):
        resp = authed_client.patch(f"/emails/{email.id}", json={"pickup_used": True})

    assert resp.status_code == 200
    mock_get.assert_awaited_once_with(email.id, _USER_ID)
    mock_archive.assert_awaited_once_with(email.account_id, email.gmail_id)


def test_list_emails_rejects_malformed_since(authed_client: TestClient) -> None:
    resp = authed_client.get("/emails?since=yesterday")
    assert resp.status_code == 422


@pytest.mark.parametrize("error", [TimeoutError("gmail timed out"), OSError("connection reset")])
def test_mark_pickup_used_survives_gmail_transport_errors(
    authed_client: TestClient, error: Exception
) -> None:
    email = _make_email()
    with (
        patch("app.routers.emails.get_email", new_callable=AsyncMock, return_value=email),
        patch("app.routers.emails.archive_gmail_message", new=AsyncMock(side_effect=error)),
        patch(
            "app.routers.emails.update_email", new_callable=AsyncMock, return_value=email
        ) as update,
    ):
        resp = authed_client.patch(f"/emails/{email.id}", json={"pickup_used": True})

    assert resp.status_code == 200
    update.assert_awaited_once()
