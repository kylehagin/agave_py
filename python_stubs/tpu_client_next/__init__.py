"""Next generation TPU client abstractions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Iterable


class ConnectionWorkersSchedulerError(Exception):
    pass


class ConnectionWorkersScheduler:
    """Distributes transactions across multiple worker connections."""

    def __init__(self) -> None:
        self.workers: Dict[str, asyncio.Queue[bytes]] = {}

    async def register_worker(self, name: str) -> None:
        self.workers[name] = asyncio.Queue()

    async def dispatch(self, tx: bytes) -> None:
        if not self.workers:
            raise ConnectionWorkersSchedulerError("no workers registered")
        # round robin for demonstration
        worker = next(iter(self.workers.values()))
        await worker.put(tx)


__all__ = ["ConnectionWorkersScheduler", "ConnectionWorkersSchedulerError"]

