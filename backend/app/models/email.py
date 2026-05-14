# backend/app/models/email.py
from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TriageCategory = Literal["action_required", "worth_reading", "auto_archive"]


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


class ContactTagInfo(BaseModel):
    """Read-only projection of a contact tag embedded in email responses.
    label is always populated: custom_label if set, else tag.capitalize()."""
    label: str
    color: str


class Email(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    gmail_id: str
    thread_id: str | None = None
    subject: str | None = None
    sender: str | None = None
    body_text: str | None = Field(default=None, exclude=True)
    received_at: datetime | None = None
    is_read: bool = False
    labels: list[str] = []
    ai_summary: str | None = None
    ai_category: str | None = None
    triage_category: TriageCategory | None = None
    triage_context: str | None = None
    deadline_extracted: str | None = None
    action_items: list[str] = []
    ai_processed: bool = False
    ai_attempts: int = 0
    last_ai_attempt_at: datetime | None = None
    is_pickup_code: bool = False
    pickup_code: str | None = None
    pickup_expiry: str | None = None
    retailer: str | None = None
    locker_location: str | None = None
    pickup_used: bool = False
    account_email: str | None = None
    is_archived: bool = False
    account_color: str | None = None
    contact_tag: ContactTagInfo | None = None
    created_at: datetime


class EmailListPage(BaseModel):
    items: list[Email]
    next_cursor: str | None


class EmailFilters(BaseModel):
    user_id: UUID
    account_id: UUID | None = None
    triage_category: TriageCategory | None = None   # maps to ai_category in current schema
    is_archived: bool = False
    since: datetime | None = None
    search: str | None = None
    sender_search: str | None = None
    has_deadline: bool = False
    deadline_after: date | None = None
    deadline_before: date | None = None
    order: Literal["received_desc", "deadline_asc"] = "received_desc"
    cursor: str | None = None
    limit: int = 50


class EmailUpdate(BaseModel):
    is_archived: bool | None = None
    pickup_used: bool | None = None


class EmailCounts(BaseModel):
    all: int
    action_required: int
    worth_reading: int
    auto_archive: int


class EmailBodyResponse(BaseModel):
    body_html: str


class PickupCodeRow(BaseModel):
    email_id: UUID
    pickup_code: str
    pickup_expiry: str | None = None
    pickup_used_at: datetime | None = None
    retailer: str | None = None
    locker_location: str | None = None
    sender_email: str | None = None
    subject: str | None = None
    received_at: datetime | None = None


class PickupCodeListResponse(BaseModel):
    items: list[PickupCodeRow]
