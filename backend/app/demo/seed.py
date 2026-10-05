from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.db.supabase import get_service_client
from app.demo.fixtures import build_demo_emails

logger = logging.getLogger(__name__)


async def seed_demo_emails(user_id: UUID, account_id: UUID) -> int:
    """Upsert the demo inbox for *user_id* under *account_id*.

    Idempotent: rows are keyed on ``(account_id, gmail_id)``.
    """
    rows = [
        {
            **email,
            "user_id": str(user_id),
            "account_id": str(account_id),
            "action_items": email.get("action_items", []),
            "is_archived": email.get("is_archived", False),
            "is_read": email.get("is_read", False),
            "is_pickup_code": email.get("is_pickup_code", False),
            "pickup_used": False,
            "labels": email.get("labels", ["INBOX"]),
        }
        for email in build_demo_emails()
    ]

    def _upsert() -> int:
        result = (
            get_service_client()
            .table("emails")
            .upsert(rows, on_conflict="account_id,gmail_id")
            .execute()
        )
        return len(result.data or [])

    count = await asyncio.to_thread(_upsert)
    logger.info("seeded %d demo emails for account %s", count, account_id)
    return count
