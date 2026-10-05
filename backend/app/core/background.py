"""Fire-and-forget task helper.

asyncio keeps only weak references to tasks, so a task created without
storing a reference can be garbage-collected before it finishes. `spawn`
holds a strong reference until completion and logs failures, which would
otherwise surface only as "Task exception was never retrieved".
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)

_running: set[asyncio.Task[Any]] = set()


def spawn(coro: Coroutine[Any, Any, Any], *, name: str) -> asyncio.Task[Any]:
    task = asyncio.create_task(coro, name=name)
    _running.add(task)
    task.add_done_callback(_on_done)
    return task


def _on_done(task: asyncio.Task[Any]) -> None:
    _running.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.error("background task %s failed", task.get_name(), exc_info=exc)
