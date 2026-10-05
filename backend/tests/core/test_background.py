from __future__ import annotations

import asyncio
import logging

import pytest

from app.core import background


async def test_spawn_runs_coroutine_and_releases_task() -> None:
    done = asyncio.Event()

    async def work() -> None:
        done.set()

    task = background.spawn(work(), name="ok-task")
    await task
    await asyncio.sleep(0)  # let the done-callback run
    assert done.is_set()
    assert task not in background._running


async def test_spawn_logs_failures_and_releases_task(caplog: pytest.LogCaptureFixture) -> None:
    async def boom() -> None:
        raise RuntimeError("kaboom")

    with caplog.at_level(logging.ERROR, logger="app.core.background"):
        task = background.spawn(boom(), name="failing-task")
        await asyncio.wait([task])
        await asyncio.sleep(0)  # let the done-callback run

    assert "failing-task" in caplog.text
    assert task not in background._running
