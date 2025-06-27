"""Small RPC load balancer used for testing."""

from __future__ import annotations

import asyncio
from typing import Iterable


class LoadBalancer:
    """Round-robin balancer for a set of RPC URLs."""

    def __init__(self, urls: Iterable[str]):
        self.urls = list(urls)
        self._idx = 0

    def next_url(self) -> str:
        if not self.urls:
            raise RuntimeError("No URLs configured")
        url = self.urls[self._idx]
        self._idx = (self._idx + 1) % len(self.urls)
        return url

    async def forward_request(self, session, request):
        """Forward ``request`` using ``session`` to the next URL."""

        url = self.next_url()
        async with session.post(url, json=request) as resp:
            return await resp.json()


__all__ = ["LoadBalancer"]

