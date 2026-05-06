# backend/tests/db/test_connected_accounts_sync.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.db.connected_accounts import list_accounts_due_for_sync, update_last_synced


@pytest.mark.asyncio
async def test_update_last_synced_calls_supabase() -> None:
    account_id = uuid4()
    now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)

    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("app.db.connected_accounts.get_service_client", return_value=mock_client):
        await update_last_synced(account_id, now)

    mock_client.table.assert_called_with("connected_accounts")
    mock_client.table().update.assert_called_once_with({"last_synced": now.isoformat()})


@pytest.mark.asyncio
async def test_list_accounts_due_for_sync_returns_list() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.is_.return_value.or_.return_value.execute.return_value.data = []

    with patch("app.db.connected_accounts.get_service_client", return_value=mock_client):
        result = await list_accounts_due_for_sync()

    assert result == []
