# backend/tests/services/test_gmail_sync.py
from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "gmail")


def load(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def test_parse_payload_plain_text() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("plain_text.json")
    result = parse_payload(msg["payload"])
    assert result == "Hello plain world"


def test_parse_payload_html_only_strips_tags() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("html_only.json")
    result = parse_payload(msg["payload"])
    assert "<p>" not in result
    assert "<b>" not in result
    assert "Hello" in result
    assert "HTML" in result
    assert "world" in result


def test_parse_payload_multipart_alternative_prefers_plain() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("multipart_alternative.json")
    result = parse_payload(msg["payload"])
    assert result == "Hello plain"


def test_parse_payload_multipart_mixed_returns_text_ignores_attachment() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("multipart_mixed.json")
    result = parse_payload(msg["payload"])
    assert result == "Email with attachment"


def test_parse_payload_multipart_related_returns_html_text() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("multipart_related.json")
    result = parse_payload(msg["payload"])
    assert "Email with image" in result
    assert "<p>" not in result


def test_parse_payload_nested_multipart_extracts_html_text() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("nested_multipart.json")
    result = parse_payload(msg["payload"])
    assert "Deeply nested HTML" in result
    assert "<p>" not in result


def test_parse_payload_image_only_returns_empty_string() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("image_only.json")
    result = parse_payload(msg["payload"])
    assert result == ""


def test_parse_payload_truncates_to_2000_chars() -> None:
    import base64
    from app.services.gmail_sync import BODY_PREVIEW_MAX_CHARS, parse_payload
    long_text = "x" * 5000
    data = base64.urlsafe_b64encode(long_text.encode()).decode()
    payload = {
        "mimeType": "text/plain",
        "headers": [],
        "body": {"size": 5000, "data": data},
        "parts": [],
    }
    result = parse_payload(payload)
    assert len(result) == BODY_PREVIEW_MAX_CHARS
    assert BODY_PREVIEW_MAX_CHARS == 2000


def test_parse_display_name_from_from_header() -> None:
    from app.services.gmail_sync import _DISPLAY_NAME_RE, _SENDER_RE

    from_header = "Amazon <noreply@amazon.com>"
    m = _SENDER_RE.search(from_header)
    assert m and m.group(1) == "noreply@amazon.com"
    n = _DISPLAY_NAME_RE.match(from_header)
    assert n and n.group(1).strip() == "Amazon"


def test_parse_quoted_display_name() -> None:
    from app.services.gmail_sync import _DISPLAY_NAME_RE

    from_header = '"John Doe" <john@example.com>'
    n = _DISPLAY_NAME_RE.match(from_header)
    assert n and n.group(1).strip() == "John Doe"


def test_no_display_name_returns_none_for_name() -> None:
    from app.services.gmail_sync import _DISPLAY_NAME_RE

    from_header = "noreply@amazon.com"
    n = _DISPLAY_NAME_RE.match(from_header)
    assert n is None


# --- sync_account integration tests ---


def _make_connected_account(user_id=None, last_synced=None, disconnected_at=None):
    from datetime import datetime, timezone
    from app.models.connected_account import ConnectedAccount, OAuthTokens
    return ConnectedAccount(
        id=uuid4(),
        user_id=user_id or uuid4(),
        provider="gmail",
        email_address="test@gmail.com",
        oauth_token=OAuthTokens(
            access_token="acc",
            refresh_token="ref",
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            scope="https://www.googleapis.com/auth/gmail.modify",
        ),
        color="#4F46E5",
        last_synced=last_synced,
        disconnected_at=disconnected_at,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


def _make_parsed_email(external_id: str = "msg1"):
    from datetime import datetime, timezone
    from app.models.email import ParsedEmail
    return ParsedEmail(
        external_id=external_id,
        sender_email="sender@example.com",
        sender_name="Sender",
        subject="Test",
        body_preview="Body",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_sync_account_inserts_messages() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()
    parsed = _make_parsed_email("msg1")

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, return_value=parsed),
        patch("app.services.gmail_sync.find_contact_tag", new_callable=AsyncMock, return_value=None),
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="inserted"),
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.fetched == 1
    assert result.inserted == 1
    assert result.updated == 0
    assert result.errors == 0


@pytest.mark.asyncio
async def test_sync_account_applies_matching_contact_tag_to_new_email() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()
    parsed = _make_parsed_email("msg1")
    tag_id = uuid4()

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, return_value=parsed),
        patch("app.services.gmail_sync.find_contact_tag", new_callable=AsyncMock, return_value=tag_id) as mock_find,
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="inserted") as mock_upsert,
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.inserted == 1
    mock_find.assert_awaited_once_with(account.user_id, "sender@example.com")
    mock_upsert.assert_awaited_once_with(account.id, account.user_id, parsed, contact_tag_id=tag_id)


@pytest.mark.asyncio
async def test_sync_account_skips_disconnected() -> None:
    from datetime import datetime, timezone
    from app.services.gmail_sync import sync_account

    account = _make_connected_account(disconnected_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

    with patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account):
        result = await sync_account(account.id)

    assert result.fetched == 0
    assert result.errors == 0


@pytest.mark.asyncio
async def test_sync_account_skips_404_messages() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1", "msg2"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, side_effect=[None, _make_parsed_email("msg2")]),
        patch("app.services.gmail_sync.find_contact_tag", new_callable=AsyncMock, return_value=None),
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="inserted"),
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.fetched == 2
    assert result.inserted == 1


@pytest.mark.asyncio
async def test_sync_account_invalid_grant_marks_disconnected() -> None:
    from app.services.gmail_sync import sync_account
    from app.services.gmail_oauth import RefreshFailed

    account = _make_connected_account()

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock,
              side_effect=RefreshFailed(is_invalid_grant=True)),
        patch("app.services.gmail_sync.mark_disconnected", new_callable=AsyncMock) as mock_mark,
    ):
        result = await sync_account(account.id)

    mock_mark.assert_awaited_once_with(account.id, "invalid_grant")
    assert result.errors > 0


@pytest.mark.asyncio
async def test_sync_account_idempotent_second_run_produces_zero_inserts() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()
    parsed = _make_parsed_email("msg1")

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, return_value=parsed),
        patch("app.services.gmail_sync.find_contact_tag", new_callable=AsyncMock, return_value=None),
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="updated"),
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.inserted == 0
    assert result.updated == 1
