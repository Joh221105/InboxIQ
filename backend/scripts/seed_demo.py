#!/usr/bin/env python3
"""Insert demo emails for a live demo.

Usage (from backend/):
    python scripts/seed_demo.py
    python scripts/seed_demo.py --user-id <uuid>
    python scripts/seed_demo.py --clear   # remove all seed emails first
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.seed import seed_demo_emails
from supabase import create_client


def get_account_id(client, user_id: str) -> str:
    result = (
        client.table("connected_accounts")
        .select("id")
        .eq("user_id", user_id)
        .is_("disconnected_at", "null")
        .order("created_at")
        .limit(1)
        .execute()
    )
    if not result.data:
        print(f"ERROR: No connected account found for user {user_id}.")
        print("Connect a Gmail account in the app first, then re-run this script.")
        sys.exit(1)
    return result.data[0]["id"]


def clear_demo_emails(client, user_id: str) -> None:
    result = (
        client.table("emails").delete().eq("user_id", user_id).like("gmail_id", "demo_%").execute()
    )
    count = len(result.data) if result.data else 0
    print(f"Cleared {count} existing demo emails.")


async def seed(user_id: str, clear: bool = False) -> None:
    from uuid import UUID

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    account_id = get_account_id(client, user_id)
    print(f"Using account {account_id} for user {user_id}")

    if clear:
        clear_demo_emails(client, user_id)

    count = await seed_demo_emails(UUID(user_id), UUID(account_id))
    print(f"Seeded {count} demo emails.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo emails for InboxIQ")
    parser.add_argument(
        "--user-id",
        default="4b02cc6c-1d4b-487d-bb4e-8e09b7fab755",
        help="Supabase user UUID",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing demo emails before inserting",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.user_id, clear=args.clear))


if __name__ == "__main__":
    main()
