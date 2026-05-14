from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.contact_tags import (
    find_contact_tag,
    normalize_identifier,
)


# ---------------------------------------------------------------------------
# normalize_identifier
# ---------------------------------------------------------------------------


def test_normalize_valid_email() -> None:
    assert normalize_identifier("Prof@UW.edu") == "prof@uw.edu"


def test_normalize_valid_email_stripped() -> None:
    assert normalize_identifier("  user@example.com  ") == "user@example.com"


def test_normalize_valid_domain() -> None:
    assert normalize_identifier("@uw.edu") == "@uw.edu"


def test_normalize_domain_lowercased() -> None:
    assert normalize_identifier("@UW.EDU") == "@uw.edu"


def test_normalize_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        normalize_identifier("   ")


def test_normalize_missing_at_raises() -> None:
    with pytest.raises(ValueError):
        normalize_identifier("notanemail")


def test_normalize_double_at_raises() -> None:
    with pytest.raises(ValueError):
        normalize_identifier("two@@signs.com")


def test_normalize_bare_at_raises() -> None:
    with pytest.raises(ValueError):
        normalize_identifier("@")


def test_normalize_domain_no_tld_raises() -> None:
    with pytest.raises(ValueError):
        normalize_identifier("@localhost")


def test_normalize_spaces_inside_raises() -> None:
    with pytest.raises(ValueError):
        normalize_identifier("user @example.com")


# ---------------------------------------------------------------------------
# find_contact_tag — specificity
# ---------------------------------------------------------------------------


def _make_tag(identifier: str, tag: str = "friend") -> object:
    from app.models.contact_tag import ContactTag
    from datetime import datetime, timezone

    return ContactTag(
        id=uuid4(),
        user_id=uuid4(),
        identifier=identifier,
        tag=tag,
        color="#000",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_find_contact_tag_full_email_beats_domain() -> None:
    domain_tag = _make_tag("@uw.edu", "friend")
    email_tag = _make_tag("prof@uw.edu", "professor")

    with patch(
        "app.services.contact_tags.db.list_user_tags",
        new=AsyncMock(return_value=[domain_tag, email_tag]),
    ):
        result = await find_contact_tag(uuid4(), "prof@uw.edu")

    assert result == email_tag.id


@pytest.mark.asyncio
async def test_find_contact_tag_domain_match_for_other_sender() -> None:
    domain_tag = _make_tag("@uw.edu", "friend")
    email_tag = _make_tag("prof@uw.edu", "professor")

    with patch(
        "app.services.contact_tags.db.list_user_tags",
        new=AsyncMock(return_value=[domain_tag, email_tag]),
    ):
        result = await find_contact_tag(uuid4(), "other@uw.edu")

    assert result == domain_tag.id


@pytest.mark.asyncio
async def test_find_contact_tag_no_match_returns_none() -> None:
    domain_tag = _make_tag("@uw.edu", "friend")

    with patch(
        "app.services.contact_tags.db.list_user_tags",
        new=AsyncMock(return_value=[domain_tag]),
    ):
        result = await find_contact_tag(uuid4(), "nobody@mit.edu")

    assert result is None


@pytest.mark.asyncio
async def test_find_contact_tag_exact_match() -> None:
    tag = _make_tag("alice@example.com", "recruiter")

    with patch(
        "app.services.contact_tags.db.list_user_tags",
        new=AsyncMock(return_value=[tag]),
    ):
        result = await find_contact_tag(uuid4(), "alice@example.com")

    assert result == tag.id


@pytest.mark.asyncio
async def test_find_contact_tag_case_insensitive() -> None:
    tag = _make_tag("alice@example.com", "recruiter")

    with patch(
        "app.services.contact_tags.db.list_user_tags",
        new=AsyncMock(return_value=[tag]),
    ):
        result = await find_contact_tag(uuid4(), "Alice@Example.COM")

    assert result == tag.id
