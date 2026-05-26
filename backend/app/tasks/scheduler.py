from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.connected_accounts import list_accounts_due_for_sync
from app.db.supabase import get_service_client
from app.services.gmail_sync import sync_account

logger = logging.getLogger(__name__)

_GLOBAL_SYNC_CONCURRENCY = 10


async def sync_all_due_accounts() -> None:
    import time

    start = time.monotonic()
    logger.info("scheduler job_start sync_all_due_accounts")

    accounts = await list_accounts_due_for_sync()
    semaphore = asyncio.Semaphore(_GLOBAL_SYNC_CONCURRENCY)

    async def _sync_one(account_id: UUID) -> object | None:
        async with semaphore:
            try:
                result = await sync_account(account_id)
                return result
            except Exception as exc:
                logger.error("Scheduler sync error for account %s: %s", account_id, exc)
                return None

    results = await asyncio.gather(*[_sync_one(a.id) for a in accounts])

    total_synced = sum(1 for r in results if r is not None)
    total_errors = sum(1 for r in results if r is None)
    elapsed = time.monotonic() - start

    logger.info(
        "scheduler job_end sync_all_due_accounts total_synced=%d total_errors=%d elapsed_s=%.2f",
        total_synced,
        total_errors,
        elapsed,
    )


async def enforce_data_retention() -> None:
    logger.info("scheduler job_start enforce_data_retention")

    def _run() -> int:
        result = get_service_client().rpc("apply_data_retention").execute()
        return int(result.data or 0)

    deleted = await asyncio.to_thread(_run)
    logger.info("scheduler job_end enforce_data_retention deleted=%s", deleted)


def make_scheduler() -> AsyncIOScheduler:
    """Create and configure a new AsyncIOScheduler instance."""
    sched = AsyncIOScheduler()
    sched.add_job(
        sync_all_due_accounts,
        "interval",
        minutes=5,
        id="sync_all_due_accounts",
    )
    sched.add_job(
        enforce_data_retention,
        "cron",
        hour=3,
        minute=0,
        id="enforce_data_retention",
    )
    return sched
