"""Simplified thread pool utilities inspired by the Rust ``thread-manager``.

The Rust crate exposes helpers for spawning work on native threads, tokio
executors and rayon pools.  The Python version provides a thin abstraction over
``concurrent.futures`` and ``asyncio``.  It is *not* a drop in replacement but
offers a familiar API.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class ThreadManagerConfig:
    """Configuration describing thread pools and event loops."""

    max_threads: int = 4
    use_asyncio: bool = True


class ThreadManager:
    """Create and manage named thread pools."""

    def __init__(self, config: Optional[ThreadManagerConfig] = None) -> None:
        self.config = config or ThreadManagerConfig()
        self._pools: Dict[str, ThreadPoolExecutor] = {}
        if self.config.use_asyncio:
            self._loop = asyncio.new_event_loop()
        else:
            self._loop = None

    def get_pool(self, name: str) -> ThreadPoolExecutor:
        if name not in self._pools:
            self._pools[name] = ThreadPoolExecutor(max_workers=self.config.max_threads)
        return self._pools[name]

    def spawn(self, func: Callable[..., Any], *args: Any, pool: str = "default", **kwargs: Any) -> Any:
        """Execute ``func`` in the specified pool."""

        executor = self.get_pool(pool)
        return executor.submit(func, *args, **kwargs)

    async def run_async(self, coro: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run an asynchronous coroutine on the manager event loop."""

        if not self._loop:
            raise RuntimeError("asyncio disabled in configuration")
        return await coro(*args, **kwargs)


__all__ = ["ThreadManager", "ThreadManagerConfig"]

