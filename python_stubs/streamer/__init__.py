"""Simple message streaming utilities using :mod:`asyncio` queues."""

import asyncio
from typing import AsyncIterator, List


class DataStreamer:
    """Broadcast messages to multiple subscribers."""

    def __init__(self) -> None:
        self._subs: List[asyncio.Queue] = []

    def subscribe(self) -> "asyncio.Queue[bytes]":
        q: "asyncio.Queue[bytes]" = asyncio.Queue()
        self._subs.append(q)
        return q

    async def publish(self, data: bytes) -> None:
        for q in list(self._subs):
            await q.put(data)

    async def listen(self, q: asyncio.Queue) -> AsyncIterator[bytes]:
        while True:
            yield await q.get()


__all__ = ["DataStreamer"]
