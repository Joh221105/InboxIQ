# backend/app/routers/emails.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.auth import UserClaims, get_current_user
from app.db.emails import list_emails
from app.models.email import EmailFilters, EmailListPage

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
async def get_emails(
    claims: UserClaims = Depends(get_current_user),
    account_id: str | None = Query(default=None),
    triage_category: str | None = Query(default=None),
    is_archived: bool = Query(default=False),
    since: str | None = Query(default=None),
    search: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> EmailListPage:
    from datetime import datetime

    filters = EmailFilters(
        user_id=claims.user_id,
        account_id=account_id,  # type: ignore[arg-type]
        triage_category=triage_category,
        is_archived=is_archived,
        since=datetime.fromisoformat(since) if since else None,
        search=search,
        cursor=cursor,
        limit=limit,
    )
    return await list_emails(filters)
