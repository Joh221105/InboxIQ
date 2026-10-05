from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ContextMode = Literal["Job Hunting", "Shopping", "School Application", "Daily"]


class User(BaseModel):
    id: UUID
    email: str
    default_context: ContextMode
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


class ContextUpdate(BaseModel):
    context: ContextMode


class ContextUpdateResponse(BaseModel):
    user: User
    job_id: str
    total: int
