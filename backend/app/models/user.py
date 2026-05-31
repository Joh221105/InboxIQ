from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class User(BaseModel):
    id: UUID
    email: str
    display_name: str | None = None
    default_context: str
    notification_tag_preferences: dict[str, bool] = Field(default_factory=dict)
    data_retention_days: int | None = None
    created_at: datetime


class UserSettingsUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    notification_tag_preferences: dict[str, bool] | None = None
    data_retention_days: int | None = Field(default=None, ge=1, le=3650)


class EmailDataDeleteCounts(BaseModel):
    emails: int
    daily_digests: int
    ai_usage: int
