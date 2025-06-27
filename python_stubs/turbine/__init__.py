"""Network data propagation utilities used by validators."""

from __future__ import annotations

import asyncio


class BroadcastStage:
    """Simplified broadcast loop."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def broadcast(self) -> None:
        while True:
            data = await self.queue.get()
            await asyncio.sleep(0)  # placeholder for network send


__all__ = ["BroadcastStage"]

