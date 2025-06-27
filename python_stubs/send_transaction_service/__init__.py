"""Asynchronous service for submitting transactions to a :class:`runtime.Runtime`.

The original Rust crate provides a complex networking service.  Here we
implement a much smaller version built on :mod:`asyncio`.  Transactions added to
the service are processed sequentially using the provided runtime instance.
"""

import asyncio
from typing import Optional

from ..runtime import Runtime, RuntimeTransaction


class SendTransactionService:
    """Queue and process transactions asynchronously."""

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self._queue: "asyncio.Queue[RuntimeTransaction]" = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None

    async def _worker(self) -> None:
        while True:
            tx = await self._queue.get()
            self.runtime.process_transaction(tx)
            self._queue.task_done()

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def send(self, tx: RuntimeTransaction) -> None:
        await self._queue.put(tx)


__all__ = ["SendTransactionService"]
