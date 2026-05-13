from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.ai import TriageResponse
from app.services.openai_client import AIInvalidResponse


@pytest.mark.asyncio
async def test_call_json_records_usage_for_invalid_json_attempt() -> None:
    from app.services.openai_client import call_json

    with (
        patch(
            "app.services.openai_client._completion",
            new=AsyncMock(side_effect=[("not json", 10, 2), ("still not json", 11, 3)]),
        ),
        patch("app.services.openai_client._record_usage", new=AsyncMock()) as record_usage,
    ):
        with pytest.raises(AIInvalidResponse):
            await call_json(
                system="system",
                user="user",
                response_model=TriageResponse,
                kind="triage",
                user_id=uuid4(),
            )

    assert record_usage.await_count == 2
