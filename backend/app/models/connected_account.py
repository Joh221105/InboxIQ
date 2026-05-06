from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OAuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str


class ConnectedAccount(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    email_address: str
    oauth_token: OAuthTokens
    color: str | None = None
    last_synced: datetime | None = None
    disconnected_at: datetime | None = None
    disconnected_reason: str | None = None
    created_at: datetime


class AccountPublic(BaseModel):
    id: UUID
    email_address: str
    provider: str
    color: str | None = None
    last_synced: datetime | None = None
    disconnected_at: datetime | None = None
