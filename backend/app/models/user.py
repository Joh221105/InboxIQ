from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: UUID
    email: str
    default_context: str
    created_at: datetime
