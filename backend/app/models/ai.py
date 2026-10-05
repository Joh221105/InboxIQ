from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TriageResponse(BaseModel):
    category: Literal["action_required", "worth_reading", "auto_archive"]
    summary: str = Field(max_length=200)
    has_deadline: bool
    has_action_items: bool
    is_pickup_code: bool


class DeadlineResponse(BaseModel):
    deadline: date | None
    deadline_text: str | None = Field(default=None, max_length=200)
    confidence: Literal["high", "medium", "low"] | None = None


class ActionItemsResponse(BaseModel):
    action_items: list[str] = Field(max_length=5)

    @field_validator("action_items")
    @classmethod
    def truncate_items(cls, v: list[str]) -> list[str]:
        return [s[:80] for s in v]


class PickupCodeResponse(BaseModel):
    pickup_code: str | None = None
    pickup_expiry: date | None = None
    retailer: str | None = None
    locker_location: str | None = None


class DigestItem(BaseModel):
    summary: str
    source_email_id: UUID
    deadline: date | None = None
    sender: str


class DigestResponse(BaseModel):
    items: list[DigestItem] = Field(max_length=5)


class Digest(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items: list[DigestItem] = Field(default_factory=list)
    degraded: bool = False
    context: str = "Daily"


class StoredDigest(BaseModel):
    user_id: UUID
    digest_date: date
    payload: Digest
    degraded: bool = False
    generated_at: datetime


@dataclass
class TriageResult:
    category: str
    summary: str
    triage_context: str
    deadline_extracted: date | None = None
    action_items: list[str] | None = None
    is_pickup_code: bool = False
    pickup_code: str | None = None
    pickup_expiry: date | None = None
    retailer: str | None = None
    locker_location: str | None = None
    cost_usd: Decimal = field(default_factory=Decimal)
