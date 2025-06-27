"""Python representation of ``banking-stage-ingress-types``."""

from __future__ import annotations

from typing import Any, List

BankingPacketBatch = List[Any]
"""Type alias mirroring the Rust ``BankingPacketBatch``."""


class BankingPacketReceiver:
    """Placeholder for the crossbeam receiver used in Rust."""

    def __init__(self) -> None:  # pragma: no cover - simple stub
        self._queue: list[BankingPacketBatch] = []

    def recv(self) -> BankingPacketBatch:
        if not self._queue:
            raise RuntimeError("queue empty")
        return self._queue.pop(0)

