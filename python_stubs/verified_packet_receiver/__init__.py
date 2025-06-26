"""UDP server that verifies received packets using HMAC.

This is a drastically simplified version of the Rust crate.  Packets are
expected to be of the form ``payload || signature`` where ``signature`` is an
HMAC-SHA256 digest of ``payload`` using a shared secret key.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
from typing import Awaitable, Callable


def _verify_packet(data: bytes, key: bytes) -> bytes | None:
    if len(data) <= 32:
        return None
    payload, signature = data[:-32], data[-32:]
    mac = hmac.new(key, payload, hashlib.sha256).digest()
    if hmac.compare_digest(mac, signature):
        return payload
    return None


async def start_server(host: str, port: int, key: bytes,
                       callback: Callable[[bytes], Awaitable[None]] | None = None) -> asyncio.AbstractServer:
    """Start a UDP server that verifies packets with ``key``."""

    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: _VerifiedProtocol(key, callback), local_addr=(host, port)
    )
    return transport, protocol


class _VerifiedProtocol(asyncio.DatagramProtocol):
    def __init__(self, key: bytes, callback: Callable[[bytes], Awaitable[None]] | None):
        self.key = key
        self.callback = callback

    def datagram_received(self, data: bytes, addr):
        payload = _verify_packet(data, self.key)
        if payload is not None and self.callback is not None:
            asyncio.create_task(self.callback(payload))


__all__ = ["start_server"]

