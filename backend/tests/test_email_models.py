# backend/tests/test_email_models.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.email import EmailFilters, ParsedEmail, SyncResult


def test_parsed_email_fields() -> None:
    p = ParsedEmail(
        external_id="abc123",
        sender_email="alice@example.com",
        subject="Hello",
        body_preview="Body text here",
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    assert p.external_id == "abc123"
    assert p.sender_email == "alice@example.com"


def test_sync_result_defaults() -> None:
    r = SyncResult(fetched=10, inserted=8, updated=2, errors=0)
    assert r.fetched == 10


def test_email_filters_defaults() -> None:
    f = EmailFilters(user_id=uuid4())
    assert f.limit == 50
    assert f.is_archived is False
