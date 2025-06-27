"""Python stubs for the `connection-cache` crate."""

from dataclasses import dataclass
from typing import Any, Dict, Tuple


class Protocol:
    """Enumeration of supported protocols."""

    UDP = "udp"
    QUIC = "quic"


@dataclass
class ConnectionCache:
    """Simplified version of the Rust ``ConnectionCache``."""

    name: str
    connection_pool_size: int = 2

    def update_key(self, key: Any) -> None:  # noqa: D401
        """Update the connection cache key."""

