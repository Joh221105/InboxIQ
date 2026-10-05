"""Run db helpers through the real supabase/postgrest query builder.

Most db tests replace the client with MagicMock, which accepts any method
chain. These tests use a real client against mocked HTTP so a chain the
pinned postgrest version does not support (for example ``.select()`` after
``.update()``) fails here instead of in production.
"""

from __future__ import annotations

import json
from uuid import uuid4

import httpx
import jwt
import pytest
import respx

from app.models.email import EmailUpdate
from app.models.user import UserSettingsUpdate
from supabase import Client, create_client

REST = "https://testproject.supabase.co/rest/v1"
USER_ID = uuid4()
NOW = "2026-05-25T12:00:00+00:00"


@pytest.fixture
def real_client(monkeypatch: pytest.MonkeyPatch) -> Client:
    key = jwt.encode(
        {"role": "service_role"}, "test-secret-at-least-32-characters!", algorithm="HS256"
    )
    client = create_client("https://testproject.supabase.co", key)
    for module in ("app.db.users", "app.db.contact_tags", "app.db.emails"):
        monkeypatch.setattr(f"{module}.get_service_client", lambda: client)
    return client


def _user_row(**overrides: object) -> dict[str, object]:
    return {
        "id": str(USER_ID),
        "email": "user@example.com",
        "default_context": "Daily",
        "notification_tag_preferences": {},
        "data_retention_days": None,
        "created_at": NOW,
        **overrides,
    }


def _tag_row(**overrides: object) -> dict[str, object]:
    return {
        "id": str(uuid4()),
        "user_id": str(USER_ID),
        "identifier": "a@b.com",
        "tag": "friend",
        "custom_label": None,
        "color": "#10B981",
        "created_at": NOW,
        **overrides,
    }


def _email_row(email_id: str, **overrides: object) -> dict[str, object]:
    return {
        "id": email_id,
        "user_id": str(USER_ID),
        "account_id": str(uuid4()),
        "gmail_id": "g-1",
        "created_at": NOW,
        "received_at": NOW,
        "is_read": False,
        "is_archived": False,
        **overrides,
    }


@respx.mock
async def test_update_default_context_returns_updated_user(real_client: Client) -> None:
    from app.db.users import update_default_context

    respx.patch(f"{REST}/users").mock(
        return_value=httpx.Response(200, json=[_user_row(default_context="Shopping")])
    )
    user = await update_default_context(USER_ID, "Shopping")
    assert user.default_context == "Shopping"


@respx.mock
async def test_update_user_settings_returns_updated_user(real_client: Client) -> None:
    from app.db.users import update_user_settings

    respx.patch(f"{REST}/users").mock(
        return_value=httpx.Response(200, json=[_user_row(data_retention_days=30)])
    )
    user = await update_user_settings(USER_ID, UserSettingsUpdate(data_retention_days=30))
    assert user.data_retention_days == 30


@respx.mock
async def test_delete_user_email_data_reports_counts(real_client: Client) -> None:
    from app.db.users import delete_user_email_data

    for table, total in (("emails", 12), ("daily_digests", 2), ("ai_usage", 40)):
        respx.delete(f"{REST}/{table}").mock(
            return_value=httpx.Response(200, json=[], headers={"Content-Range": f"*/{total}"})
        )
    counts = await delete_user_email_data(USER_ID)
    assert counts.model_dump() == {"emails": 12, "daily_digests": 2, "ai_usage": 40}


@respx.mock
async def test_create_tag_returns_inserted_tag(real_client: Client) -> None:
    from app.db.contact_tags import create_tag

    row = _tag_row()
    respx.post(f"{REST}/contact_tags").mock(return_value=httpx.Response(201, json=[row]))
    tag = await create_tag(
        user_id=USER_ID, identifier="a@b.com", tag="friend", custom_label=None, color="#10B981"
    )
    assert str(tag.id) == row["id"]


@respx.mock
async def test_update_tag_returns_updated_tag_or_none(real_client: Client) -> None:
    from app.db.contact_tags import update_tag

    row = _tag_row(color="#000000")
    route = respx.patch(f"{REST}/contact_tags")
    route.mock(return_value=httpx.Response(200, json=[row]))
    updated = await update_tag(uuid4(), USER_ID, {"color": "#000000"})
    assert updated is not None and updated.color == "#000000"

    route.mock(return_value=httpx.Response(200, json=[]))
    assert await update_tag(uuid4(), USER_ID, {"color": "#000000"}) is None


@respx.mock
async def test_update_email_marks_read(real_client: Client) -> None:
    from app.db.emails import update_email

    email_id = str(uuid4())
    respx.get(f"{REST}/emails").mock(
        return_value=httpx.Response(200, json=_email_row(email_id, is_read=True))
    )
    patch_route = respx.patch(f"{REST}/emails").mock(
        return_value=httpx.Response(200, json=[_email_row(email_id, is_read=True)])
    )
    updated = await update_email(email_id, USER_ID, EmailUpdate(is_read=True))
    assert patch_route.called
    assert updated is not None and updated.is_read is True


@respx.mock
async def test_mark_ai_failed_counts_attempts(real_client: Client) -> None:
    from app.db.emails import mark_ai_failed

    email_id = uuid4()
    respx.post(f"{REST}/rpc/increment_ai_attempts").mock(return_value=httpx.Response(204))
    respx.get(f"{REST}/emails").mock(return_value=httpx.Response(200, json={"ai_attempts": 3}))
    patch_route = respx.patch(f"{REST}/emails").mock(return_value=httpx.Response(200, json=[]))

    attempts = await mark_ai_failed(email_id)

    assert attempts == 3
    sent = patch_route.calls.last.request.content.decode()
    assert '"ai_processed":false' in sent.replace(" ", "")
    assert "(AI unavailable)" in sent


@respx.mock
async def test_marking_pickup_used_also_archives(real_client: Client) -> None:
    from app.db.emails import update_email

    email_id = str(uuid4())
    respx.get(f"{REST}/emails").mock(
        return_value=httpx.Response(
            200, json=_email_row(email_id, pickup_used=True, is_archived=True)
        )
    )
    patch_route = respx.patch(f"{REST}/emails").mock(return_value=httpx.Response(200, json=[]))

    updated = await update_email(email_id, USER_ID, EmailUpdate(pickup_used=True))

    sent = json.loads(patch_route.calls.last.request.content)
    assert sent["pickup_used"] is True
    assert sent["is_archived"] is True
    assert sent["pickup_used_at"] is not None
    assert updated is not None and updated.is_archived is True


@respx.mock
async def test_create_tag_maps_unique_violation_to_conflict(real_client: Client) -> None:
    from app.core.errors import ConflictError
    from app.db.contact_tags import create_tag

    respx.post(f"{REST}/contact_tags").mock(
        return_value=httpx.Response(
            409,
            json={"code": "23505", "message": "duplicate key value", "details": None, "hint": None},
        )
    )
    with pytest.raises(ConflictError) as exc:
        await create_tag(
            user_id=USER_ID, identifier="a@b.com", tag="friend", custom_label=None, color="#10B981"
        )
    assert exc.value.code == "duplicate_contact"


_NO_ROWS = httpx.Response(
    406,
    json={
        "code": "PGRST116",
        "details": "The result contains 0 rows",
        "hint": None,
        "message": "JSON object requested, multiple (or no) rows returned",
    },
)


@respx.mock
async def test_get_email_returns_none_when_no_row_matches(real_client: Client) -> None:
    from app.db.emails import get_email

    respx.get(f"{REST}/emails").mock(return_value=_NO_ROWS)
    assert await get_email(uuid4(), USER_ID) is None


@respx.mock
async def test_get_account_raises_not_found_when_no_row_matches(
    real_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.errors import NotFoundError
    from app.db.connected_accounts import get_account

    monkeypatch.setattr("app.db.connected_accounts.get_service_client", lambda: real_client)
    respx.get(f"{REST}/connected_accounts").mock(return_value=_NO_ROWS)
    with pytest.raises(NotFoundError):
        await get_account(uuid4())


@respx.mock
async def test_get_digest_returns_none_when_no_row_matches(real_client: Client) -> None:
    from app.core.clock import utc_today
    from app.db.emails import get_digest

    respx.get(f"{REST}/daily_digests").mock(return_value=_NO_ROWS)
    assert await get_digest(USER_ID, utc_today()) is None
