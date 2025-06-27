"""Simplified Python API for the `quic-client` crate."""

from dataclasses import dataclass
from typing import Any


@dataclass
class QuicClientConnection:
    """Placeholder connection object."""

    address: str

    def send(self, data: bytes) -> None:
        """Send data to the server (no-op)."""
        pass


class QuicClient:
    """Simplified QUIC client."""

    @staticmethod
    def connect(address: str) -> QuicClientConnection:
        """Return a placeholder connection."""
        return QuicClientConnection(address)
