from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.db.contact_tags import UniqueViolation
from app.main import app
from app.models.contact_tag import ContactTag
from app.services.contact_tags import JOBS, ContactTagJob

_USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_OTHER_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _make_tag(
    identifier: str = "alice@example.com",
    tag: str = "recruiter",
    user_id: UUID | None = None,
) -> ContactTag:
    return ContactTag(
        id=uuid4(),
        user_id=user_id or _USER_ID,
        identifier=identifier,
        tag=tag,
        color="#F59E0B",
        created_at=datetime.now(UTC),
    )


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    JOBS.clear()


# ---------------------------------------------------------------------------
# POST /contacts
# ---------------------------------------------------------------------------


def test_post_contact_happy_path(authed_client: TestClient) -> None:
    tag = _make_tag()
    with (
        patch("app.routers.contacts.create_tag", new=AsyncMock(return_value=tag)),
        patch("app.routers.contacts.count_emails_for_identifier", new=AsyncMock(return_value=5)),
        patch("app.routers.contacts.apply_retroactive_sync", new=AsyncMock(return_value=5)),
    ):
        resp = authed_client.post(
            "/contacts",
            json={"identifier": "alice@example.com", "tag": "recruiter"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["tag"]["identifier"] == "alice@example.com"
    assert data["retroactive_count"] == 5
    assert data["job_id"] is None


def test_post_contact_normalizes_identifier(authed_client: TestClient) -> None:
    tag = _make_tag(identifier="alice@example.com")
    with (
        patch("app.routers.contacts.create_tag", new=AsyncMock(return_value=tag)) as mock_create,
        patch("app.routers.contacts.count_emails_for_identifier", new=AsyncMock(return_value=0)),
        patch("app.routers.contacts.apply_retroactive_sync", new=AsyncMock(return_value=0)),
    ):
        authed_client.post(
            "/contacts",
            json={"identifier": " Alice@EXAMPLE.COM ", "tag": "recruiter"},
        )
    # Normalized identifier was passed to create_tag
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["identifier"] == "alice@example.com"


def test_post_contact_duplicate_returns_409(authed_client: TestClient) -> None:
    with patch("app.routers.contacts.create_tag", new=AsyncMock(side_effect=UniqueViolation)):
        resp = authed_client.post(
            "/contacts",
            json={"identifier": "alice@example.com", "tag": "recruiter"},
        )
    assert resp.status_code == 409


def test_post_contact_invalid_identifier_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/contacts",
        json={"identifier": "notanemail", "tag": "recruiter"},
    )
    assert resp.status_code == 422


def test_post_contact_invalid_tag_type_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/contacts",
        json={"identifier": "alice@example.com", "tag": "unknown"},
    )
    assert resp.status_code == 422


def test_post_contact_count_above_threshold_returns_job_id(authed_client: TestClient) -> None:
    tag = _make_tag()
    with (
        patch("app.routers.contacts.create_tag", new=AsyncMock(return_value=tag)),
        patch("app.routers.contacts.count_emails_for_identifier", new=AsyncMock(return_value=200)),
        patch("app.routers.contacts.apply_retroactive_async", new=AsyncMock(return_value="abc123")),
    ):
        resp = authed_client.post(
            "/contacts",
            json={"identifier": "alice@example.com", "tag": "recruiter"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "abc123"
    assert data["retroactive_count"] == 200


def test_post_contact_custom_requires_label(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/contacts",
        json={"identifier": "alice@example.com", "tag": "custom"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /contacts
# ---------------------------------------------------------------------------


def test_get_contacts_returns_grouped(authed_client: TestClient) -> None:
    recruiter_tag = _make_tag(tag="recruiter")
    friend_tag = _make_tag(identifier="bob@example.com", tag="friend")

    with patch(
        "app.routers.contacts.list_user_tags",
        new=AsyncMock(return_value=[recruiter_tag, friend_tag]),
    ):
        resp = authed_client.get("/contacts")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["recruiter"]) == 1
    assert len(data["friend"]) == 1
    assert data["professor"] == []
    assert data["custom"] == []


# ---------------------------------------------------------------------------
# DELETE /contacts/{id}
# ---------------------------------------------------------------------------


def test_delete_own_tag_returns_204(authed_client: TestClient) -> None:
    tag_id = uuid4()
    with patch("app.routers.contacts.delete_tag", new=AsyncMock(return_value=True)):
        resp = authed_client.delete(f"/contacts/{tag_id}")
    assert resp.status_code == 204


def test_delete_other_users_tag_returns_404(authed_client: TestClient) -> None:
    tag_id = uuid4()
    with patch("app.routers.contacts.delete_tag", new=AsyncMock(return_value=False)):
        resp = authed_client.delete(f"/contacts/{tag_id}")
    assert resp.status_code == 404


def test_patch_contact_updates_label_and_color(authed_client: TestClient) -> None:
    tag = ContactTag(
        id=uuid4(),
        user_id=_USER_ID,
        identifier="prof@uw.edu",
        tag="professor",
        custom_label="My Prof",
        color="#FF0000",
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    with patch("app.routers.contacts.update_tag", new=AsyncMock(return_value=tag)):
        resp = authed_client.patch(
            f"/contacts/{tag.id}",
            json={"custom_label": "My Prof", "color": "#FF0000"},
        )

    assert resp.status_code == 200
    assert resp.json()["custom_label"] == "My Prof"
    assert resp.json()["color"] == "#FF0000"


def test_patch_contact_not_found(authed_client: TestClient) -> None:
    with patch("app.routers.contacts.update_tag", new=AsyncMock(return_value=None)):
        resp = authed_client.patch(
            f"/contacts/{uuid4()}",
            json={"custom_label": "X"},
        )

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /contacts/jobs/{job_id}
# ---------------------------------------------------------------------------


def test_get_contact_job_for_owner(authed_client: TestClient) -> None:
    job = ContactTagJob(job_id="job1", user_id=_USER_ID, total=50, processed=30)
    JOBS["job1"] = job

    resp = authed_client.get("/contacts/jobs/job1")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["processed"] == 30
    assert data["total"] == 50


def test_get_contact_job_for_other_user_returns_404(authed_client: TestClient) -> None:
    job = ContactTagJob(job_id="job2", user_id=_OTHER_ID, total=10)
    JOBS["job2"] = job

    resp = authed_client.get("/contacts/jobs/job2")

    assert resp.status_code == 404
