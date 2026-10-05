from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.config import settings
from app.models.ai import TriageResponse
from app.services.ai_client import (
    ANTHROPIC_MODEL,
    OPENROUTER_MODEL,
    AIInvalidResponse,
    Completion,
    call_json,
)
from app.services.ai_client import (
    _completion as provider_completion,
)


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


def _from(model: str, content: str) -> Completion:
    return Completion(
        content=content,
        model=model,
        prompt_tokens=10,
        completion_tokens=5,
        cost_usd=Decimal("0"),
    )


def _skipped_primary(completion: AsyncMock) -> list[bool]:
    return [call.kwargs.get("skip_primary", False) for call in completion.await_args_list]


@pytest.mark.parametrize(
    "unusable",
    ["not json", json.dumps({"result": "ok"})],
    ids=["malformed_json", "schema_mismatch"],
)
async def test_call_json_asks_the_fallback_after_unusable_primary_output(unusable: str) -> None:
    completion = AsyncMock(
        side_effect=[_from(OPENROUTER_MODEL, unusable), _from(ANTHROPIC_MODEL, VALID)]
    )
    with (
        patch("app.services.ai_client._completion", new=completion),
        patch("app.services.ai_client._record_usage", new=AsyncMock()) as record_usage,
        patch.object(settings, "anthropic_api_key", "test-anthropic-key"),
    ):
        result = await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )

    assert result.category == "action_required"
    assert _skipped_primary(completion) == [False, True]
    assert record_usage.await_count == 2


async def test_call_json_retries_the_primary_when_no_fallback_is_configured() -> None:
    completion = AsyncMock(
        side_effect=[_from(OPENROUTER_MODEL, "not json"), _from(OPENROUTER_MODEL, VALID)]
    )
    with (
        patch("app.services.ai_client._completion", new=completion),
        patch("app.services.ai_client._record_usage", new=AsyncMock()),
        patch.object(settings, "anthropic_api_key", ""),
    ):
        result = await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )

    assert result.category == "action_required"
    assert _skipped_primary(completion) == [False, False]


async def test_call_json_gives_up_when_the_fallback_output_is_unusable_too() -> None:
    completion = AsyncMock(
        side_effect=[_from(OPENROUTER_MODEL, "not json"), _from(ANTHROPIC_MODEL, "still not json")]
    )
    with (
        patch("app.services.ai_client._completion", new=completion),
        patch("app.services.ai_client._record_usage", new=AsyncMock()),
        patch.object(settings, "anthropic_api_key", "test-anthropic-key"),
        pytest.raises(AIInvalidResponse),
    ):
        await call_json(
            system="s", user="u", response_model=TriageResponse, kind="triage", user_id=uuid4()
        )

    assert completion.await_count == 2


async def test_completion_goes_straight_to_the_fallback_when_asked_to_skip_the_primary() -> None:
    openrouter = AsyncMock(return_value=(VALID, 10, 5))
    anthropic = AsyncMock(return_value=(VALID, 10, 5))
    with (
        patch("app.services.ai_client._completion_openrouter", new=openrouter),
        patch("app.services.ai_client._completion_anthropic", new=anthropic),
        patch.object(settings, "openrouter_api_key", "test-openrouter-key"),
        patch.object(settings, "anthropic_api_key", "test-anthropic-key"),
    ):
        completion = await provider_completion("s", "u", skip_primary=True)

    openrouter.assert_not_awaited()
    assert completion.model == ANTHROPIC_MODEL
