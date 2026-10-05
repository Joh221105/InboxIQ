"""LLM access for JSON-producing prompts.

OpenRouter (free tier) is tried first, with Anthropic Claude Haiku as the
fallback, both when OpenRouter is unavailable and when its answer cannot be
used. Every response is parsed as JSON and validated against a Pydantic model
before use, and every call is recorded in ``ai_usage`` for cost tracking.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeVar
from uuid import UUID

import anthropic as _anthropic_sdk
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from app.core.config import settings
from app.db.supabase import get_service_client

logger = logging.getLogger(__name__)

# OpenRouter free-tier model (primary)
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"
# Anthropic Claude Haiku (fallback – cheapest Claude model)
ANTHROPIC_MODEL = "claude-haiku-4-5"

# Anthropic Haiku 4.5 pricing: $1/1M input, $5/1M output
_HAIKU_INPUT_PER_1K = Decimal("0.001")
_HAIKU_OUTPUT_PER_1K = Decimal("0.005")

T = TypeVar("T", bound=BaseModel)

_openrouter_client: AsyncOpenAI | None = None
_anthropic_client: _anthropic_sdk.AsyncAnthropic | None = None


class AIInvalidResponse(Exception):
    pass


class AIServiceUnavailable(Exception):
    pass


@dataclass(frozen=True)
class Completion:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: Decimal


# Free models occasionally wrap, truncate or mis-shape JSON; one more attempt
# recovers most of those. It goes to the fallback provider when there is one.
_JSON_ATTEMPTS = 2


def _get_openrouter_client() -> AsyncOpenAI:
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            timeout=30,
        )
    return _openrouter_client


def _get_anthropic_client() -> _anthropic_sdk.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = _anthropic_sdk.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
        )
    return _anthropic_client


def _usage_cost_anthropic(input_tokens: int, output_tokens: int) -> Decimal:
    cost = (Decimal(input_tokens) / 1000 * _HAIKU_INPUT_PER_1K) + (
        Decimal(output_tokens) / 1000 * _HAIKU_OUTPUT_PER_1K
    )
    return round(cost, 6)


def _extract_json(text: str) -> str:
    """Strip markdown code fences that some free models emit around JSON."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end]).strip()
    return text


async def _record_usage(
    completion: Completion,
    *,
    kind: str,
    user_id: UUID,
    email_id: UUID | None,
) -> None:
    payload = {
        "user_id": str(user_id),
        "email_id": str(email_id) if email_id else None,
        "kind": kind,
        "model": completion.model,
        "prompt_tokens": completion.prompt_tokens,
        "completion_tokens": completion.completion_tokens,
        "cost_usd": str(completion.cost_usd),
    }

    def _insert() -> None:
        get_service_client().table("ai_usage").insert(payload).execute()

    try:
        await asyncio.to_thread(_insert)
    except Exception:
        # Usage tracking must never fail the AI call it describes.
        logger.exception("failed to write ai_usage kind=%s user_id=%s", kind, user_id)


async def _completion_openrouter(system: str, user: str) -> tuple[str, int, int]:
    try:
        resp = await _get_openrouter_client().chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            timeout=30,
        )
    except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
        raise AIServiceUnavailable(str(exc)) from exc
    except Exception as exc:
        logger.exception("openrouter error")
        raise AIServiceUnavailable(str(exc)) from exc

    content = resp.choices[0].message.content or ""
    usage = resp.usage
    return content, usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0


async def _completion_anthropic(system: str, user: str) -> tuple[str, int, int]:
    try:
        resp = await _get_anthropic_client().messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except (_anthropic_sdk.APITimeoutError, _anthropic_sdk.RateLimitError) as exc:
        raise AIServiceUnavailable(str(exc)) from exc
    except _anthropic_sdk.APIError as exc:
        logger.exception("anthropic error")
        raise AIServiceUnavailable(str(exc)) from exc

    content = next((b.text for b in resp.content if b.type == "text"), "")
    return content, resp.usage.input_tokens, resp.usage.output_tokens


async def _completion(system: str, user: str, *, skip_primary: bool = False) -> Completion:
    """Try OpenRouter first, then fall back to Anthropic.

    ``skip_primary`` goes straight to the fallback, for a second attempt after
    the primary answered with output that could not be used.
    """
    if settings.openrouter_api_key and not skip_primary:
        try:
            content, pt, ct = await _completion_openrouter(system, user)
            return Completion(content, OPENROUTER_MODEL, pt, ct, Decimal(0))
        except AIServiceUnavailable:
            logger.warning("openrouter unavailable, falling back to anthropic")

    if settings.anthropic_api_key:
        content, pt, ct = await _completion_anthropic(system, user)
        return Completion(content, ANTHROPIC_MODEL, pt, ct, _usage_cost_anthropic(pt, ct))

    raise AIServiceUnavailable(
        "no AI provider configured — set OPENROUTER_API_KEY or ANTHROPIC_API_KEY"
    )


async def call_json(
    *,
    system: str,
    user: str,
    response_model: type[T],
    kind: str,
    user_id: UUID,
    email_id: UUID | None = None,
) -> T:
    parsed, _cost = await call_json_with_cost(
        system=system,
        user=user,
        response_model=response_model,
        kind=kind,
        user_id=user_id,
        email_id=email_id,
    )
    return parsed


@retry(
    retry=retry_if_exception_type(AIServiceUnavailable),
    wait=wait_random_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def call_json_with_cost(
    *,
    system: str,
    user: str,
    response_model: type[T],
    kind: str,
    user_id: UUID,
    email_id: UUID | None = None,
) -> tuple[T, Decimal]:
    total_cost = Decimal(0)
    skip_primary = False
    failure = AIInvalidResponse("model did not return a usable response")
    for _attempt in range(_JSON_ATTEMPTS):
        completion = await _completion(system, user, skip_primary=skip_primary)
        total_cost += completion.cost_usd
        await _record_usage(completion, kind=kind, user_id=user_id, email_id=email_id)
        try:
            return _parse(completion.content, response_model, kind=kind), total_cost
        except AIInvalidResponse as exc:
            failure = exc
            # Asking the same free model again rarely helps, so the next
            # attempt goes to the fallback when one is configured.
            skip_primary = completion.model == OPENROUTER_MODEL and bool(settings.anthropic_api_key)
    raise failure


def _parse(raw: str, response_model: type[T], *, kind: str) -> T:
    try:
        data = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        # Log a short sample only: responses can contain email content.
        logger.warning("ai returned invalid json kind=%s sample=%r", kind, raw[:200])
        raise AIInvalidResponse("model did not return valid JSON") from exc

    try:
        return response_model.model_validate(data)
    except ValidationError as exc:
        logger.warning("ai response failed validation kind=%s err=%s", kind, exc)
        raise AIInvalidResponse(str(exc)) from exc
