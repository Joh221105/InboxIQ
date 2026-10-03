from __future__ import annotations

import logging
from datetime import date, datetime
from html import escape
from typing import Literal
from uuid import UUID

import google.auth.exceptions
import httplib2
import httpx
from fastapi import APIRouter, Depends, Query
from googleapiclient.errors import HttpError

from app.core.auth import UserClaims, get_current_user
from app.core.errors import NotFoundError
from app.db.emails import get_email, get_email_counts, list_emails, update_email
from app.models.email import (
    Email,
    EmailBodyResponse,
    EmailCounts,
    EmailFilters,
    EmailListPage,
    EmailUpdate,
    TriageCategory,
)
from app.services.email_body import fetch_email_body_html, sanitize_body_html
from app.services.gmail_oauth import RefreshFailed
from app.services.gmail_sync import archive_gmail_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emails", tags=["emails"])

# Errors the Gmail client can raise for an unreachable or rejecting API: HTTP
# status errors, token refresh failures, and transport errors from httplib2,
# google-auth and the OS (timeouts, resets).
_GMAIL_FAILURES = (
    HttpError,
    RefreshFailed,
    httpx.HTTPError,
    httplib2.HttpLib2Error,
    google.auth.exceptions.TransportError,
    OSError,
)


@router.get("")
async def get_emails(
    claims: UserClaims = Depends(get_current_user),
    account_id: UUID | None = Query(default=None),
    contact_tag_id: UUID | None = Query(default=None),
    triage_category: TriageCategory | None = Query(default=None),
    is_archived: bool = Query(default=False),
    since: datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    sender_search: str | None = Query(default=None),
    has_deadline: bool = Query(default=False),
    deadline_after: date | None = Query(default=None),
    deadline_before: date | None = Query(default=None),
    order: Literal["received_desc", "deadline_asc"] = Query(default="received_desc"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> EmailListPage:
    filters = EmailFilters(
        user_id=claims.user_id,
        account_id=account_id,
        contact_tag_id=contact_tag_id,
        triage_category=triage_category,
        is_archived=is_archived,
        since=since,
        search=search,
        sender_search=sender_search,
        has_deadline=has_deadline,
        deadline_after=deadline_after,
        deadline_before=deadline_before,
        order=order,
        cursor=cursor,
        limit=limit,
    )
    return await list_emails(filters)


@router.get("/counts")
async def counts(claims: UserClaims = Depends(get_current_user)) -> EmailCounts:
    return await get_email_counts(claims.user_id)


@router.patch("/{email_id}")
async def patch_email(
    email_id: UUID,
    body: EmailUpdate,
    claims: UserClaims = Depends(get_current_user),
) -> Email:
    if body.pickup_used is True:
        existing = await get_email(email_id, claims.user_id)
        if existing is None:
            raise NotFoundError("Email not found.")
        try:
            await archive_gmail_message(existing.account_id, existing.gmail_id)
        except _GMAIL_FAILURES:
            # Marking the code used matters more than archiving it in Gmail.
            logger.warning("gmail archive failed for email_id=%s; marking used anyway", email_id)
    updated = await update_email(email_id, claims.user_id, body)
    if updated is None:
        raise NotFoundError("Email not found.")
    return updated


@router.get("/{email_id}/body")
async def get_email_body(
    email_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> EmailBodyResponse:
    email = await get_email(email_id, claims.user_id)
    # get_email already filters by user; the ownership re-check is defense in depth.
    if email is None or email.user_id != claims.user_id:
        raise NotFoundError("Email not found.")

    if email.gmail_id.startswith("demo_"):
        text = email.body_text or ""
        body_html = (
            "<div style='font-family:sans-serif;font-size:14px;line-height:1.6;"
            "color:#1a1a1a;white-space:pre-wrap;padding:4px 0'>"
            f"{escape(text)}</div>"
        )
        return EmailBodyResponse(body_html=body_html)

    body_html = await fetch_email_body_html(email.account_id, email.gmail_id)
    # Re-sanitize at the response boundary in case the cached body predates a sanitizer change.
    return EmailBodyResponse(body_html=sanitize_body_html(body_html))
