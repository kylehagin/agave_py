"""Thread pool implementation used by :mod:`unified_scheduler_logic`."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Optional


class SchedulerPool:
    """Lightweight wrapper around :class:`ThreadPoolExecutor`."""

    def __init__(self, workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=workers)

    def submit(self, func: Callable, *args, **kwargs):
        """Submit a callable to be executed in the pool."""

        return self._executor.submit(func, *args, **kwargs)

    def map(self, func: Callable, iterable: Iterable):
        """Map ``func`` over ``iterable`` using the pool."""

        return self._executor.map(func, iterable)

    def shutdown(self, wait: bool = True):
        self._executor.shutdown(wait=wait)


__all__ = ["SchedulerPool"]

