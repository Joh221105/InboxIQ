from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class User(BaseModel):
    id: UUID
    email: str
    default_context: str
    notification_tag_preferences: dict[str, bool] = Field(default_factory=dict)
    data_retention_days: int | None = None
    created_at: datetime


class UserSettingsUpdate(BaseModel):
    notification_tag_preferences: dict[str, bool] | None = None
    data_retention_days: int | None = Field(default=None, ge=1, le=3650)


class EmailDataDeleteCounts(BaseModel):
    emails: int
    daily_digests: int
    ai_usage: int
