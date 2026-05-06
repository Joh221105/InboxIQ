# backend/app/models/email.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ParsedEmail(BaseModel):
    external_id: str          # maps to emails.gmail_id
    sender_email: str         # maps to emails.sender (always lowercased)
    subject: str
    body_preview: str         # maps to emails.body_text
    received_at: datetime


class SyncResult(BaseModel):
    fetched: int
    inserted: int
    updated: int
    errors: int


class Email(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    gmail_id: str
    thread_id: str | None = None
    subject: str | None = None
    sender: str | None = None
    received_at: datetime | None = None
    is_read: bool = False
    labels: list[str] = []
    ai_summary: str | None = None
    ai_category: str | None = None
    is_archived: bool = False
    account_color: str | None = None
    created_at: datetime


class EmailListPage(BaseModel):
    items: list[Email]
    next_cursor: str | None


class EmailFilters(BaseModel):
    user_id: UUID
    account_id: UUID | None = None
    triage_category: str | None = None   # maps to ai_category
    is_archived: bool = False
    since: datetime | None = None
    search: str | None = None
    cursor: str | None = None
    limit: int = 50
