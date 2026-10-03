from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.user import UserSettingsUpdate


@pytest.mark.asyncio
async def test_update_user_settings_updates_only_provided_fields() -> None:
    from app.db.users import update_user_settings

    user_id = uuid4()
    updates: list[dict] = []

    class _Result:
        data = [
            {
                "id": str(user_id),
                "email": "user@example.com",
                "default_context": "Daily",
                "notification_tag_preferences": {"recruiter": True},
                "data_retention_days": None,
                "created_at": datetime(2026, 5, 25, tzinfo=UTC).isoformat(),
            }
        ]

    class _Chain:
        def update(self, changes):
            updates.append(changes)
            return self

        def eq(self, *_args):
            return self

        def select(self, _fields):
            return self

        def execute(self):
            return _Result()

    class _Client:
        def table(self, name):
            assert name == "users"
            return _Chain()

    from unittest.mock import patch

    with patch("app.db.users.get_service_client", return_value=_Client()):
        user = await update_user_settings(
            user_id,
            UserSettingsUpdate(notification_tag_preferences={"recruiter": True}),
        )

    assert updates == [{"notification_tag_preferences": {"recruiter": True}}]
    assert user.notification_tag_preferences == {"recruiter": True}
    assert user.data_retention_days is None


@pytest.mark.asyncio
async def test_delete_user_email_data_deletes_owned_rows_and_returns_counts() -> None:
    from app.db.users import delete_user_email_data

    user_id = uuid4()
    tables: list[str] = []

    class _Result:
        def __init__(self, count: int) -> None:
            self.count = count

    class _Chain:
        def __init__(self, count: int) -> None:
            self._count = count

        def delete(self, *, count):
            assert count == "exact"
            return self

        def eq(self, column, value):
            assert column == "user_id"
            assert value == str(user_id)
            return self

        def execute(self):
            return _Result(self._count)

    class _Client:
        def table(self, name):
            tables.append(name)
            counts = {"emails": 4, "daily_digests": 1, "ai_usage": 2}
            return _Chain(counts[name])

    from unittest.mock import patch

    with patch("app.db.users.get_service_client", return_value=_Client()):
        counts = await delete_user_email_data(user_id)

    assert sorted(tables) == ["ai_usage", "daily_digests", "emails"]
    assert counts.emails == 4
    assert counts.daily_digests == 1
    assert counts.ai_usage == 2
