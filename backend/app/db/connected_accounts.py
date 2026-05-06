from __future__ import annotations

from uuid import UUID

from app.models.connected_account import ConnectedAccount, OAuthTokens


async def get_account(account_id: UUID) -> ConnectedAccount:
    """Fetch a connected account row by primary key."""
    raise NotImplementedError


async def update_oauth_token(account_id: UUID, tokens: OAuthTokens) -> None:
    """Persist refreshed OAuth tokens for an account."""
    raise NotImplementedError
