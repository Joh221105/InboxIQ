# backend/tests/db/test_emails.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.email import EmailFilters, ParsedEmail


@pytest.mark.asyncio
async def test_upsert_email_calls_rpc_and_returns_inserted() -> None:
    from app.db.emails import upsert_email

    account_id = uuid4()
    user_id = uuid4()
    parsed = ParsedEmail(
        external_id="gmail123",
        sender_email="alice@example.com",
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
            "p_body_text": "Body",
            "p_received_at": "2025-06-01T00:00:00+00:00",
        },
    )


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
