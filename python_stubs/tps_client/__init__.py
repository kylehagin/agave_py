"""Client helpers for submitting transactions at high throughput."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, Optional


class TpsClientError(Exception):
    """Base error for the TPS client."""


class TpsClient:
    """Asynchronous interface mirroring the Rust trait."""

    def __init__(self, rpc_url: str) -> None:
        self.rpc_url = rpc_url

    async def send_transaction(self, tx: bytes) -> str:
        await asyncio.sleep(0)
        return "SIGNATURE"

    async def send_batch(self, transactions: Iterable[bytes]) -> None:
        await asyncio.gather(*(self.send_transaction(tx) for tx in transactions))

    async def get_latest_blockhash(self) -> str:
        await asyncio.sleep(0)
        return "BLOCKHASH"


__all__ = ["TpsClient", "TpsClientError"]

