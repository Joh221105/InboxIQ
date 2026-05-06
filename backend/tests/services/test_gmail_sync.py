# backend/tests/services/test_gmail_sync.py
from __future__ import annotations

import json
import os

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
