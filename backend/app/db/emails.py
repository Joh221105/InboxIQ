# backend/app/db/emails.py (STUB - will be replaced in Task 7)
from __future__ import annotations

from typing import Literal
from uuid import UUID

from app.models.email import ParsedEmail


async def upsert_email(account_id: UUID, user_id: UUID, parsed: ParsedEmail) -> Literal["inserted", "updated"]:
    raise NotImplementedError
