"""Utility for spinning up an in-process validator for tests."""

import asyncio
from typing import Optional

from validator_py import Validator


class TestValidator:
    """Wrap :class:`validator_py.Validator` with convenience helpers."""

    def __init__(self) -> None:
        self.validator = Validator()
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        self._task = asyncio.create_task(self.validator.start())

    async def stop(self) -> None:
        if self._task:
            self.validator.rpc.stop()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


__all__ = ["TestValidator"]
