from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.ai import TriageResponse
from app.services.openai_client import AIInvalidResponse


@pytest.mark.asyncio
async def test_call_json_returns_parsed_model_on_valid_response() -> None:
    import json

    from app.services.openai_client import call_json

    valid_payload = json.dumps(
        {
            "category": "action_required",
            "summary": "Recruiter invites you to schedule an interview.",
            "has_deadline": True,
            "has_action_items": True,
            "is_pickup_code": False,
        }
    )

    with (
        patch(
            "app.services.openai_client._completion",
            new=AsyncMock(return_value=(valid_payload, 50, 20)),
        ),
        patch("app.services.openai_client._record_usage", new=AsyncMock()),
    ):
        result = await call_json(
            system="system",
            user="user",
            response_model=TriageResponse,
            kind="triage",
            user_id=uuid4(),
        )

    assert result.category == "action_required"
    assert result.has_deadline is True
    assert result.is_pickup_code is False


@pytest.mark.asyncio
async def test_call_json_raises_ai_invalid_response_on_schema_mismatch() -> None:
    import json

    from app.services.openai_client import call_json

    # Valid JSON but missing required fields for TriageResponse
    bad_payload = json.dumps({"result": "ok"})

    with (
        patch(
            "app.services.openai_client._completion",
            new=AsyncMock(return_value=(bad_payload, 10, 5)),
        ),
        patch("app.services.openai_client._record_usage", new=AsyncMock()),
        pytest.raises(AIInvalidResponse),
    ):
        await call_json(
            system="system",
            user="user",
            response_model=TriageResponse,
            kind="triage",
            user_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_call_json_records_usage_for_invalid_json_attempt() -> None:
    from app.services.openai_client import call_json

    with (
        patch(
            "app.services.openai_client._completion",
            new=AsyncMock(side_effect=[("not json", 10, 2), ("still not json", 11, 3)]),
        ),
        patch("app.services.openai_client._record_usage", new=AsyncMock()) as record_usage,
        pytest.raises(AIInvalidResponse),
    ):
        await call_json(
            system="system",
            user="user",
            response_model=TriageResponse,
            kind="triage",
            user_id=uuid4(),
        )

    assert record_usage.await_count == 2
