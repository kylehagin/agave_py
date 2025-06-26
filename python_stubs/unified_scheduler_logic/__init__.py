"""Very small task scheduler logic.

This module implements a minimal asynchronous task scheduler using
``asyncio``.  It allows scheduling callables to be executed after a certain
delay.  The real ``unified-scheduler-logic`` crate provides far more
functionality.  Only a subset that is useful for tests and examples is
implemented here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List


TaskCallback = Callable[[], Awaitable[None]]


@dataclass
class ScheduledTask:
    callback: TaskCallback
    delay: float


class Scheduler:
    """Simple asyncio based scheduler."""

    def __init__(self) -> None:
        self._tasks: List[ScheduledTask] = []

    def schedule(self, callback: TaskCallback, delay: float) -> None:
        """Schedule ``callback`` to run after ``delay`` seconds."""

        self._tasks.append(ScheduledTask(callback, delay))

    async def run(self) -> None:
        """Run all scheduled tasks."""

        for task in list(self._tasks):
            await asyncio.sleep(task.delay)
            await task.callback()


__all__ = ["Scheduler"]

