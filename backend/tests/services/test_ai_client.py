from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.ai import TriageResponse
from app.services.ai_client import AIInvalidResponse, Completion, call_json


def _completion(content: str) -> Completion:
    return Completion(
        content=content,
        model="test-model",
        prompt_tokens=10,
        completion_tokens=5,
        cost_usd=Decimal("0"),
    )


VALID = json.dumps(
    {
        "category": "action_required",
        "summary": "Recruiter invites you to schedule an interview.",
        "has_deadline": True,
        "has_action_items": True,
        "is_pickup_code": False,
    }
)


async def test_call_json_returns_parsed_model_on_valid_response() -> None:
    with (
        patch("app.services.ai_client._completion", new=AsyncMock(return_value=_completion(VALID))),
        patch("app.services.ai_client._record_usage", new=AsyncMock()),
    ):
        result = await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )
    assert result.category == "action_required"


async def test_call_json_raises_ai_invalid_response_on_schema_mismatch() -> None:
    with (
        patch(
            "app.services.ai_client._completion",
            new=AsyncMock(return_value=_completion(json.dumps({"result": "ok"}))),
        ),
        patch("app.services.ai_client._record_usage", new=AsyncMock()),
        pytest.raises(AIInvalidResponse),
    ):
        await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )


async def test_call_json_retries_invalid_json_once_and_records_both_attempts() -> None:
    completion = AsyncMock(side_effect=[_completion("not json"), _completion("still not json")])
    with (
        patch("app.services.ai_client._completion", new=completion),
        patch("app.services.ai_client._record_usage", new=AsyncMock()) as record_usage,
        pytest.raises(AIInvalidResponse),
    ):
        await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )
    assert completion.await_count == 2
    assert record_usage.await_count == 2


async def test_call_json_recovers_when_second_attempt_is_valid() -> None:
    completion = AsyncMock(
        side_effect=[_completion("```json\nnope"), _completion(f"```json\n{VALID}\n```")]
    )
    with (
        patch("app.services.ai_client._completion", new=completion),
        patch("app.services.ai_client._record_usage", new=AsyncMock()),
    ):
        result = await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )
    assert result.has_action_items is True
