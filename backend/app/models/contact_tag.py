from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

TagType = Literal["professor", "friend", "recruiter", "custom"]

_DOMAIN_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")
_EMAIL_RE = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")


def normalize_identifier(value: str) -> str:
    """Lower-case an email address or ``@domain`` identifier and validate it."""
    identifier = value.strip().lower()
    if not identifier:
        raise ValueError("identifier cannot be empty")
    if identifier.startswith("@"):
        if not _DOMAIN_RE.match(identifier[1:]):
            raise ValueError(f"invalid domain identifier: {identifier!r}")
        return identifier
    if not _EMAIL_RE.match(identifier):
        raise ValueError(f"invalid email identifier: {identifier!r}")
    return identifier


class ContactTag(BaseModel):
    id: UUID
    user_id: UUID
    identifier: str
    tag: TagType
    custom_label: str | None = None
    color: str
    created_at: datetime


class ContactTagCreate(BaseModel):
    identifier: str
    tag: TagType
    custom_label: str | None = None
    color: str | None = None

    @field_validator("identifier")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return normalize_identifier(value)

    @model_validator(mode="after")
    def _custom_needs_label(self) -> ContactTagCreate:
        if self.tag == "custom" and not self.custom_label:
            raise ValueError("custom_label is required for custom tags")
        return self


class ContactTagUpdate(BaseModel):
    custom_label: str | None = None
    color: str | None = None

    @model_validator(mode="after")
    def _requires_change(self) -> ContactTagUpdate:
        if self.custom_label is None and self.color is None:
            raise ValueError("provide custom_label or color")
        return self

    def changes(self) -> dict[str, str]:
        return self.model_dump(exclude_none=True)


class ContactsGrouped(BaseModel):
    professor: list[ContactTag] = []
    friend: list[ContactTag] = []
    recruiter: list[ContactTag] = []
    custom: list[ContactTag] = []


class CreateContactResponse(BaseModel):
    tag: ContactTag
    retroactive_count: int
    job_id: str | None = None
