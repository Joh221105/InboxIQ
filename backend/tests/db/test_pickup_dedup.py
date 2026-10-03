from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest


class _Result:
    def __init__(self, data: list[dict]) -> None:
        self.data = data


class _PickupQuery:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.eq_filters: list[tuple[str, object]] = []
        self.gte_filters: list[tuple[str, object]] = []
        self.orders: list[tuple[str, bool]] = []

    def select(self, *_args: object) -> _PickupQuery:
        return self

    def eq(self, column: str, value: object) -> _PickupQuery:
        self.eq_filters.append((column, value))
        return self

    def gte(self, column: str, value: object) -> _PickupQuery:
        self.gte_filters.append((column, value))
        return self

    def or_(self, expression: str) -> _PickupQuery:
        if "pickup_expiry.gte." in expression:
            self.gte_filters.append(("pickup_expiry", expression.rsplit(".", 1)[-1]))
        return self

    def not_(self, *_args: object) -> _PickupQuery:
        return self

    def order(self, column: str, desc: bool = False) -> _PickupQuery:
        self.orders.append((column, desc))
        return self

    def execute(self) -> _Result:
        rows = list(self.rows)
        for column, value in self.eq_filters:
            if column == "connected_accounts.user_id":
                continue
            rows = [row for row in rows if row.get(column) == value]
        for column, value in self.gte_filters:
            rows = [row for row in rows if row.get(column) is None or row.get(column) >= value]
        rows.sort(key=lambda row: (row["pickup_code"], -_timestamp(row["received_at"])))
        return _Result(rows)


class _Client:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def table(self, name: str) -> _PickupQuery:
        assert name == "emails"
        return _PickupQuery(self.rows)


def _timestamp(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _row(
    *,
    pickup_code: str,
    received_at: str,
    pickup_used: bool = False,
    pickup_expiry: str | None = None,
) -> dict:
    return {
        "id": str(uuid4()),
        "pickup_code": pickup_code,
        "pickup_expiry": pickup_expiry,
        "pickup_used_at": None,
        "retailer": "Amazon",
        "locker_location": "Pine Hub Locker",
        "sender": "ship@amazon.com",
        "subject": "Your pickup code",
        "received_at": received_at,
        "is_pickup_code": True,
        "pickup_used": pickup_used,
    }


@pytest.mark.asyncio
async def test_list_pickup_codes_deduplicates_by_code_keeping_most_recent() -> None:
    from app.db.emails import list_pickup_codes

    user_id = uuid4()
    older = _row(pickup_code="123456", received_at="2026-05-10T12:00:00Z")
    newer = _row(pickup_code="123456", received_at="2026-05-12T12:00:00Z")

    with patch("app.db.emails.get_service_client", return_value=_Client([older, newer])):
        result = await list_pickup_codes(user_id, used=False)

    assert len(result) == 1
    assert str(result[0].email_id) == newer["id"]
    assert result[0].pickup_code == "123456"


@pytest.mark.asyncio
async def test_list_pickup_codes_filters_used_state() -> None:
    from app.db.emails import list_pickup_codes

    user_id = uuid4()
    active = _row(pickup_code="ACTIVE", received_at="2026-05-12T12:00:00Z", pickup_used=False)
    used = _row(pickup_code="USED", received_at="2026-05-12T12:00:00Z", pickup_used=True)

    with patch("app.db.emails.get_service_client", return_value=_Client([active, used])):
        result = await list_pickup_codes(user_id, used=False)

    assert [item.pickup_code for item in result] == ["ACTIVE"]


@pytest.mark.asyncio
async def test_list_pickup_codes_hides_expired_unless_included() -> None:
    from app.db.emails import list_pickup_codes

    user_id = uuid4()
    expired = _row(
        pickup_code="OLD",
        received_at="2026-05-12T12:00:00Z",
        pickup_expiry=date(2020, 1, 1).isoformat(),
    )

    with patch("app.db.emails.get_service_client", return_value=_Client([expired])):
        hidden = await list_pickup_codes(user_id, used=False, include_expired=False)
        shown = await list_pickup_codes(user_id, used=False, include_expired=True)

    assert hidden == []
    assert [item.pickup_code for item in shown] == ["OLD"]
