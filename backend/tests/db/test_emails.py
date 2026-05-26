# backend/tests/db/test_emails.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.models.email import Email, EmailFilters, EmailUpdate, ParsedEmail


@pytest.mark.asyncio
async def test_upsert_email_calls_rpc_and_returns_inserted() -> None:
    from app.db.emails import upsert_email

    account_id = uuid4()
    user_id = uuid4()
    parsed = ParsedEmail(
        external_id="gmail123",
        sender_email="alice@example.com",
        sender_name="Alice",
        subject="Hello",
        body_preview="Body",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )

    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = "inserted"

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        result = await upsert_email(account_id, user_id, parsed)

    assert result == "inserted"
    mock_client.rpc.assert_called_once_with(
        "upsert_email_record",
        {
            "p_account_id": str(account_id),
            "p_user_id": str(user_id),
            "p_gmail_id": "gmail123",
            "p_subject": "Hello",
            "p_sender": "alice@example.com",
            "p_sender_name": "Alice",
            "p_body_text": "Body",
            "p_contact_tag_id": None,
            "p_received_at": "2025-06-01T00:00:00+00:00",
        },
    )


@pytest.mark.asyncio
async def test_upsert_email_passes_contact_tag_id_to_rpc() -> None:
    from app.db.emails import upsert_email

    account_id = uuid4()
    user_id = uuid4()
    tag_id = uuid4()
    parsed = ParsedEmail(
        external_id="gmail123",
        sender_email="alice@example.com",
        sender_name="Alice",
        subject="Hello",
        body_preview="Body",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )

    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = "inserted"

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        await upsert_email(account_id, user_id, parsed, contact_tag_id=tag_id)

    assert mock_client.rpc.call_args[0][1]["p_contact_tag_id"] == str(tag_id)


@pytest.mark.asyncio
async def test_list_emails_returns_empty_for_no_results() -> None:
    from app.db.emails import list_emails

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        result = await list_emails(EmailFilters(user_id=uuid4()))

    assert result.items == []
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_get_email_returns_none_for_missing() -> None:
    from app.db.emails import get_email

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        result = await get_email(uuid4(), uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_update_email_marks_pickup_used_as_archived() -> None:
    from app.db.emails import update_email

    user_id = uuid4()
    email_id = uuid4()
    existing = Email(
        id=email_id,
        user_id=user_id,
        account_id=uuid4(),
        gmail_id="gmail-1",
        subject="Pickup ready",
        sender="locker@example.com",
        body_text="Code 123456",
        received_at=datetime(2026, 5, 25, tzinfo=timezone.utc),
        is_pickup_code=True,
        pickup_code="123456",
        pickup_used=False,
        is_archived=False,
        created_at=datetime(2026, 5, 25, tzinfo=timezone.utc),
    )
    updates: list[dict] = []

    class _Result:
        data = {
            **existing.model_dump(
                mode="json",
                exclude={"account_color", "account_email", "contact_tag"},
            ),
            "pickup_used": True,
            "is_archived": True,
            "pickup_used_at": "2026-05-25T12:00:00+00:00",
        }

    class _Chain:
        def update(self, changes):
            updates.append(changes)
            return self

        def eq(self, *_args):
            return self

        def select(self, *_args):
            return self

        def maybe_single(self):
            return self

        def execute(self):
            return _Result()

    class _Client:
        def table(self, name):
            assert name == "emails"
            return _Chain()

    with (
        patch("app.db.emails.get_email", new=AsyncMock(return_value=existing)),
        patch("app.db.emails.get_service_client", return_value=_Client()),
    ):
        updated = await update_email(email_id, user_id, EmailUpdate(pickup_used=True))

    assert updates[-1]["pickup_used"] is True
    assert updates[-1]["is_archived"] is True
    assert updates[-1]["pickup_used_at"] is not None
    assert updated is not None
    assert updated.pickup_used is True
    assert updated.is_archived is True


@pytest.mark.asyncio
async def test_update_email_includes_is_read_change() -> None:
    from app.db.emails import update_email

    user_id = uuid4()
    email_id = uuid4()
    existing = Email(
        id=email_id,
        user_id=user_id,
        account_id=uuid4(),
        gmail_id="gmail-1",
        subject="Message",
        sender="sender@example.com",
        received_at=datetime(2026, 5, 25, tzinfo=timezone.utc),
        is_read=False,
        created_at=datetime(2026, 5, 25, tzinfo=timezone.utc),
    )
    updates: list[dict] = []

    class _Result:
        data = {
            **existing.model_dump(
                mode="json",
                exclude={"account_color", "account_email", "contact_tag"},
            ),
            "is_read": True,
        }

    class _Chain:
        def update(self, changes):
            updates.append(changes)
            return self

        def eq(self, *_args):
            return self

        def select(self, *_args):
            return self

        def maybe_single(self):
            return self

        def execute(self):
            return _Result()

    class _Client:
        def table(self, name):
            assert name == "emails"
            return _Chain()

    with (
        patch("app.db.emails.get_email", new=AsyncMock(return_value=existing)),
        patch("app.db.emails.get_service_client", return_value=_Client()),
    ):
        updated = await update_email(email_id, user_id, EmailUpdate(is_read=True))

    assert updates[-1]["is_read"] is True
    assert updated is not None
    assert updated.is_read is True


@pytest.mark.asyncio
async def test_list_emails_filters_by_exact_contact_tag_id() -> None:
    from app.db.emails import list_emails

    user_id = uuid4()
    contact_tag_id = uuid4()
    eq_calls: list[tuple[str, str | bool]] = []

    class _Result:
        data: list[dict] = []

    class _Chain:
        def select(self, *_args):
            return self

        def eq(self, column, value):
            eq_calls.append((column, value))
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args):
            return self

        def execute(self):
            return _Result()

    class _Client:
        def table(self, name):
            assert name == "emails"
            return _Chain()

    with patch("app.db.emails.get_service_client", return_value=_Client()):
        await list_emails(EmailFilters(user_id=user_id, contact_tag_id=contact_tag_id))

    assert ("contact_tag_id", str(contact_tag_id)) in eq_calls


@pytest.mark.asyncio
async def test_mark_ai_failed_after_third_attempt_keeps_email_retryable() -> None:
    from app.db.emails import mark_ai_failed

    email_id = UUID("12345678-1234-5678-1234-567812345678")
    updates: list[dict] = []

    class _Result:
        data = {"ai_attempts": 2}

    class _Chain:
        def update(self, changes):
            updates.append(changes)
            return self

        def eq(self, *_args):
            return self

        def select(self, *_args):
            return self

        def maybe_single(self):
            return self

        def execute(self):
            return _Result()

    class _Client:
        def table(self, name):
            assert name == "emails"
            return _Chain()

    with patch("app.db.emails.get_service_client", return_value=_Client()):
        attempts = await mark_ai_failed(email_id)

    assert attempts == 3
    assert updates[-1]["ai_attempts"] == 3
    assert updates[-1]["ai_processed"] is False
    assert updates[-1]["ai_summary"] == "(AI unavailable)"


def test_build_contact_tag_none_input_returns_none() -> None:
    from app.db.emails import _build_contact_tag

    assert _build_contact_tag(None) is None


def test_build_contact_tag_uses_custom_label_when_set() -> None:
    from app.db.emails import _build_contact_tag

    result = _build_contact_tag({"tag": "recruiter", "custom_label": "Recruiter", "color": "#ff0000"})
    assert result is not None
    assert result.label == "Recruiter"
    assert result.color == "#ff0000"


def test_build_contact_tag_capitalizes_tag_when_custom_label_is_none() -> None:
    from app.db.emails import _build_contact_tag

    result = _build_contact_tag({"tag": "recruiter", "custom_label": None, "color": None})
    assert result is not None
    assert result.label == "Recruiter"
    assert result.color == "#6b7280"


def test_sanitize_fts_strips_tsquery_operators() -> None:
    from app.db.emails import _sanitize_fts_input

    assert _sanitize_fts_input("') OR 1=1 --") == "OR 1 1"


def test_sanitize_fts_keeps_alphanumeric_and_spaces() -> None:
    from app.db.emails import _sanitize_fts_input

    assert _sanitize_fts_input("amazon order") == "amazon order"


def test_sanitize_fts_strips_special_chars() -> None:
    from app.db.emails import _sanitize_fts_input

    assert _sanitize_fts_input("hello!world&foo|bar") == "hello world foo bar"


def test_sanitize_fts_none_returns_none() -> None:
    from app.db.emails import _sanitize_fts_input

    assert _sanitize_fts_input(None) is None


def test_sanitize_fts_empty_string_returns_none() -> None:
    from app.db.emails import _sanitize_fts_input

    assert _sanitize_fts_input("   ") is None
