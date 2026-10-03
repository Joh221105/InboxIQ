from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

from app.db import emails as emails_db
from app.db.emails import get_email_counts

COUNTS = {None: 2500, "action_required": 40, "worth_reading": 300, "auto_archive": 2160}


class _CountQuery:
    def __init__(self) -> None:
        self.category: str | None = None
        self.select_kwargs: dict[str, Any] = {}

    def select(self, *_columns: str, **kwargs: Any) -> _CountQuery:
        self.select_kwargs = kwargs
        return self

    def eq(self, column: str, value: Any) -> _CountQuery:
        if column == "ai_category":
            self.category = value
        return self

    def execute(self) -> SimpleNamespace:
        assert self.select_kwargs == {"count": "exact", "head": True}
        return SimpleNamespace(data=[], count=COUNTS[self.category])


async def test_counts_use_exact_count_queries_without_a_row_cap() -> None:
    emails_db._counts_cache.clear()
    client = SimpleNamespace(table=lambda _name: _CountQuery())
    with patch("app.db.emails.get_service_client", return_value=client):
        counts = await get_email_counts(uuid4())
    assert counts.model_dump() == {
        "all": 2500,
        "action_required": 40,
        "worth_reading": 300,
        "auto_archive": 2160,
    }
