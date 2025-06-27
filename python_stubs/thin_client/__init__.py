"""Minimal Python implementation mirroring the Rust ``thin-client`` crate.

This module exposes a :class:`ThinClient` class that communicates with a
validator's RPC endpoint and TPU (transaction processing unit).  The real Rust
implementation performs heavy networking and concurrency.  The Python version
sketches the same API using :mod:`asyncio` for asynchronous operations.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class ClientOptimizer:
    """Very small stand in for the Rust optimizer used to rotate RPC clients."""

    index: int = 0

    def best(self) -> int:
        return self.index


class ThinClient:
    """Communicates with the RPC service and the TPU.

    Parameters mirror the Rust constructor.  Networking is done lazily using
    ``asyncio`` so calls such as :py:meth:`send_transaction` return ``awaitable``
    objects.
    """

    def __init__(self, rpc_addr: str, tpu_addr: str) -> None:
        self.rpc_addr = rpc_addr
        self.tpu_addr = tpu_addr
        self._optimizer = ClientOptimizer()

    async def get_latest_blockhash(self) -> str:
        """Return a dummy blockhash.

        A real implementation would perform an RPC request.  The async nature
        mirrors the network bound Rust version.
        """

        await asyncio.sleep(0)
        return "BLOCKHASH"

    async def send_transaction(self, tx_bytes: bytes) -> str:
        """Send a transaction to the TPU.

        The real crate sends the binary representation of a transaction over
        UDP or QUIC.  Here we simply simulate the delay.
        """

        await asyncio.sleep(0)
        # Return dummy signature
        return "SIGNATURE"

    async def send_batch(self, batch: Iterable[bytes]) -> None:
        """Send many transactions in parallel."""

        await asyncio.gather(*(self.send_transaction(tx) for tx in batch))


__all__ = ["ThinClient", "ClientOptimizer"]

