"""Minimal utilities for XDP-style packet capture.

The real Rust crate interfaces with the Linux kernel's eXpress Data Path (XDP)
for high performance packet processing.  Python does not expose XDP directly so
this module provides a tiny fallback based on raw sockets.  It is sufficient for
tests but not for production use.
"""

from __future__ import annotations

import socket
from typing import Iterator


def capture_packets(interface: str) -> Iterator[bytes]:
    """Yield raw packets received on ``interface``.

    TODO: replace with real XDP bindings.
    """

    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    sock.bind((interface, 0))
    try:
        while True:
            data = sock.recv(65535)
            yield data
    finally:
        sock.close()


__all__ = ["capture_packets"]

