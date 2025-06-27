"""Simplified UDP client implementation.

This module provides a small wrapper around Python's :mod:`socket` module to
send and receive UDP datagrams.  The goal is to mimic the very small subset of
functionality that Agave's ``udp-client`` crate exposes.  Cryptographic packet
verification or more advanced connection pooling is **not** implemented yet.
"""

from __future__ import annotations

import socket
from typing import Optional, Tuple


class UDPClient:
    """Basic UDP client supporting send and receive operations."""

    def __init__(self, remote_addr: Tuple[str, int]):
        self.remote_addr = remote_addr
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data: bytes) -> None:
        """Send ``data`` to the remote address."""

        self._sock.sendto(data, self.remote_addr)

    def recv(self, bufsize: int = 2048) -> Tuple[bytes, Tuple[str, int]]:
        """Receive a datagram from the socket."""

        return self._sock.recvfrom(bufsize)

    def close(self) -> None:
        self._sock.close()


def create_client(host: str, port: int) -> UDPClient:
    """Helper to create a :class:`UDPClient` from host/port values."""

    return UDPClient((host, port))


__all__ = ["UDPClient", "create_client"]

