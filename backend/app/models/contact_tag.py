from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ContactTag(BaseModel):
    id: UUID
    user_id: UUID
    identifier: str
    tag: str
    custom_label: str | None = None
    color: str
    created_at: datetime


class ContactTagCreate(BaseModel):
    identifier: str
    tag: str
    custom_label: str | None = None
    color: str | None = None


class ContactTagUpdate(BaseModel):
    custom_label: str | None = None
    color: str | None = None


class ContactsGrouped(BaseModel):
    professor: list[ContactTag] = []
    friend: list[ContactTag] = []
    recruiter: list[ContactTag] = []
    custom: list[ContactTag] = []


class CreateContactResponse(BaseModel):
    tag: ContactTag
    retroactive_count: int
    job_id: str | None = None


class ContactJobStatus(BaseModel):
    job_id: str
    status: str
    processed: int
    total: int
