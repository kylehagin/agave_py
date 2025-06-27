"""Helpers for creating TLS contexts similar to the Rust ``tls-utils`` crate."""

from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Optional, Tuple


def tls_client_context() -> ssl.SSLContext:
    """Return an insecure :class:`ssl.SSLContext` used for client connections."""

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def tls_server_context(certfile: str, keyfile: str) -> ssl.SSLContext:
    """Return a simple server :class:`ssl.SSLContext`."""

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile, keyfile)
    return context


@dataclass
class QuicClientCertificate:
    """Placeholder representing a QUIC client certificate."""

    certificate: bytes
    key: bytes

    @classmethod
    def generate(cls) -> "QuicClientCertificate":
        """Return dummy certificate bytes."""

        return cls(b"cert", b"key")


__all__ = [
    "tls_client_context",
    "tls_server_context",
    "QuicClientCertificate",
]

