from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import TypeVar
from uuid import UUID

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from app.core.config import settings
from app.db.supabase import get_service_client

logger = logging.getLogger(__name__)

GPT4O_INPUT_PER_1K = 0.0025
GPT4O_OUTPUT_PER_1K = 0.010
MODEL = "gpt-4o"

T = TypeVar("T", bound=BaseModel)
_client: AsyncOpenAI | None = None


class AIInvalidResponse(Exception):
    pass


class AIServiceUnavailable(Exception):
    pass


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30)
    return _client


def _usage_cost(prompt_tokens: int, completion_tokens: int) -> Decimal:
    cost = (prompt_tokens / 1000 * GPT4O_INPUT_PER_1K) + (
        completion_tokens / 1000 * GPT4O_OUTPUT_PER_1K
    )
    return Decimal(str(round(cost, 6)))


async def _record_usage(
    *,
    user_id: UUID,
    email_id: UUID | None,
    kind: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    payload = {
        "user_id": str(user_id),
        "email_id": str(email_id) if email_id else None,
        "kind": kind,
        "model": MODEL,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": str(_usage_cost(prompt_tokens, completion_tokens)),
    }

    def _insert() -> None:
        get_service_client().table("ai_usage").insert(payload).execute()

    try:
        await asyncio.to_thread(_insert)
    except Exception:
        logger.exception("failed to write ai_usage kind=%s user_id=%s", kind, user_id)


async def _completion(system: str, user: str) -> tuple[str, int, int]:
    try:
        resp = await _get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            seed=42,
            temperature=0,
            timeout=30,
        )
    except (openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError) as exc:
        raise AIServiceUnavailable(str(exc)) from exc
    except openai.OpenAIError as exc:
        logger.exception("non-retriable openai error")
        raise AIServiceUnavailable(str(exc)) from exc

    content = resp.choices[0].message.content or ""
    usage = resp.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return content, prompt_tokens, completion_tokens


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
    raw, prompt_tokens, completion_tokens = await _completion(system, user)
    cost = _usage_cost(prompt_tokens, completion_tokens)
    await _record_usage(
        user_id=user_id,
        email_id=email_id,
        kind=kind,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raw, prompt_tokens, completion_tokens = await _completion(system, user)
        cost += _usage_cost(prompt_tokens, completion_tokens)
        await _record_usage(
            user_id=user_id,
            email_id=email_id,
            kind=kind,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("invalid json from openai kind=%s raw=%s", kind, raw)
            raise AIInvalidResponse(str(exc)) from exc

    try:
        parsed = response_model.model_validate(data)
    except ValidationError as exc:
        logger.warning("invalid openai response kind=%s raw=%s err=%s", kind, raw, exc)
        raise AIInvalidResponse(str(exc)) from exc

    return parsed, cost
