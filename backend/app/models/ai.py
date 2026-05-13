from __future__ import annotations

from datetime import date, datetime
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
    items: list[DigestItem] = Field(default_factory=list)
    degraded: bool = False


class StoredDigest(BaseModel):
    user_id: UUID
    digest_date: date
    payload: Digest
    degraded: bool = False
    generated_at: datetime
