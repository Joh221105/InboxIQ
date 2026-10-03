from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.errors import BadRequestError
from app.db.emails import _decode_cursor, _encode_cursor, _keyset_filter, list_emails
from app.models.email import EmailFilters

_USER = uuid4()


_DEFAULT_CATEGORY = {1: "action_required", 2: "worth_reading", 3: "auto_archive"}


def _row(
    rank: int, received_at: str, email_id: str | None = None, *, unclassified: bool = False
) -> dict[str, Any]:
    # Mirrors migration 022: unclassified mail ranks with worth_reading (2).
    category = None if unclassified else _DEFAULT_CATEGORY[rank]
    return {
        "id": email_id or str(uuid4()),
        "user_id": str(_USER),
        "account_id": str(uuid4()),
        "gmail_id": f"g-{uuid4().hex[:8]}",
        "created_at": received_at,
        "received_at": received_at,
        "ai_category": category,
        "triage_rank": rank,
    }


class RecordingQuery:
    """Fake PostgREST builder: records calls and returns the given rows."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str):
        def method(*args: Any, **kwargs: Any) -> RecordingQuery:
            self.calls.append((name, args, kwargs))
            return self

        return method

    def execute(self) -> SimpleNamespace:
        return SimpleNamespace(data=[dict(r) for r in self.rows])


def _client(query: RecordingQuery) -> SimpleNamespace:
    return SimpleNamespace(table=lambda _name: query)


async def _list(query: RecordingQuery, **filters: Any):
    with patch("app.db.emails.get_service_client", return_value=_client(query)):
        return await list_emails(EmailFilters(user_id=_USER, **filters))


async def test_orders_by_triage_rank_then_recency_in_the_database() -> None:
    query = RecordingQuery([])
    await _list(query)
    orders = [(args, kwargs) for name, args, kwargs in query.calls if name == "order"]
    assert orders == [
        (("triage_rank",), {"desc": False}),
        (("received_at",), {"desc": True}),
        (("id",), {"desc": True}),
    ]


async def test_returns_rows_in_database_order_with_cursor_from_last_row() -> None:
    rows = [
        _row(1, "2026-05-01T10:00:00+00:00"),
        _row(2, "2026-05-03T10:00:00+00:00"),
        _row(2, "2026-05-02T10:00:00+00:00"),
    ]
    page = await _list(RecordingQuery(rows), limit=2)
    assert [str(e.id) for e in page.items] == [rows[0]["id"], rows[1]["id"]]
    assert page.next_cursor is not None
    cursor = _decode_cursor(page.next_cursor)
    assert (cursor.rank, cursor.received_at, cursor.email_id) == (
        2,
        "2026-05-03T10:00:00+00:00",
        rows[1]["id"],
    )


async def test_last_page_has_no_cursor() -> None:
    page = await _list(RecordingQuery([_row(1, "2026-05-01T10:00:00+00:00")]), limit=2)
    assert page.next_cursor is None


async def test_cursor_becomes_keyset_filter() -> None:
    last = _row(2, "2026-05-03T10:00:00+00:00")
    query = RecordingQuery([])
    await _list(query, cursor=_encode_cursor(last))
    or_calls = [args[0] for name, args, _ in query.calls if name == "or_"]
    assert or_calls == [_keyset_filter(_decode_cursor(_encode_cursor(last)))]


async def test_invalid_cursor_raises_bad_request() -> None:
    with pytest.raises(BadRequestError) as exc:
        await _list(RecordingQuery([]), cursor="not-a-cursor")
    assert exc.value.code == "invalid_cursor"


async def test_deadline_order_is_not_paginated() -> None:
    rows = [_row(1, "2026-05-01T10:00:00+00:00"), _row(1, "2026-05-02T10:00:00+00:00")]
    page = await _list(RecordingQuery(rows), order="deadline_asc", limit=1)
    assert page.next_cursor is None
    with pytest.raises(BadRequestError):
        await _list(RecordingQuery([]), order="deadline_asc", cursor=_encode_cursor(rows[0]))


_KEYSET_RE = re.compile(
    r'^triage_rank\.gt\.(\d+),and\(triage_rank\.eq\.\1,received_at\.lt\."([^"]+)"\),'
    r'and\(triage_rank\.eq\.\1,received_at\.eq\."\2",id\.lt\.([0-9a-f-]+)\)$'
)


class EvaluatingQuery(RecordingQuery):
    """Applies the real ORDER BY and keyset predicate so pages can be walked."""

    def execute(self) -> SimpleNamespace:
        rows = sorted(self.rows, key=lambda r: r["id"], reverse=True)
        rows = sorted(rows, key=lambda r: r["received_at"], reverse=True)
        rows = sorted(rows, key=lambda r: r["triage_rank"])
        for name, args, _ in self.calls:
            if name == "or_":
                match = _KEYSET_RE.match(args[0])
                assert match, args[0]
                rank, ts, eid = int(match[1]), match[2], match[3]
                rows = [
                    r
                    for r in rows
                    if r["triage_rank"] > rank
                    or (r["triage_rank"] == rank and r["received_at"] < ts)
                    or (r["triage_rank"] == rank and r["received_at"] == ts and r["id"] < eid)
                ]
            if name == "limit":
                rows = rows[: args[0]]
        return SimpleNamespace(data=[dict(r) for r in rows])


async def test_walking_pages_visits_every_email_exactly_once() -> None:
    same_time = "2026-05-02T09:00:00+00:00"
    rows = [
        _row(1, "2026-05-01T08:00:00+00:00"),
        _row(3, "2026-05-05T08:00:00+00:00"),
        _row(2, same_time),
        _row(2, same_time),
        _row(1, "2026-05-04T08:00:00+00:00"),
        _row(2, "2026-05-06T08:00:00+00:00", unclassified=True),
        _row(2, "2026-05-03T08:00:00+00:00"),
    ]
    seen: list[str] = []
    cursor: str | None = None
    while True:
        page = await _list(EvaluatingQuery(rows), limit=2, cursor=cursor)
        seen.extend(str(e.id) for e in page.items)
        if page.next_cursor is None:
            break
        cursor = page.next_cursor
    assert sorted(seen) == sorted(r["id"] for r in rows)
    assert len(seen) == len(set(seen))


def _raw_cursor(payload: dict[str, Any]) -> str:
    import base64
    import json

    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


@pytest.mark.parametrize(
    "payload",
    [
        {"r": 1, "t": "2026-05-01T10:00:00+00:00", "i": 123},  # non-string id
        {"r": 1, "t": "garbage", "i": str(uuid4())},  # unparseable timestamp
        {
            "r": 1,
            "t": '2026-05-01"),user_id.neq.0,and(id.eq."',
            "i": str(uuid4()),
        },  # filter injection
        {"r": 4, "t": "2026-05-01T10:00:00+00:00", "i": str(uuid4())},  # rank out of range
    ],
)
async def test_tampered_cursor_payloads_raise_bad_request(payload: dict[str, Any]) -> None:
    with pytest.raises(BadRequestError) as exc:
        await _list(RecordingQuery([]), cursor=_raw_cursor(payload))
    assert exc.value.code == "invalid_cursor"


def test_keyset_filter_uses_normalized_timestamp() -> None:
    cursor = _decode_cursor(_raw_cursor({"r": 2, "t": "2026-05-01T10:00:00Z", "i": str(uuid4())}))
    assert cursor.received_at == "2026-05-01T10:00:00+00:00"
