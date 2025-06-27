"""Simplified RPC client mirroring the `rpc-client` crate."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class HttpSender:
    url: str

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send an HTTP RPC request (no-op)."""
        return {}


class RpcClient:
    """Minimal RPC client wrapper."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.sender = HttpSender(url)

    def get_account(self, pubkey: str) -> Dict[str, Any]:
        """Fetch an account by pubkey (placeholder)."""
        return {}
