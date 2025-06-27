"""Python facade for the Rust crate `client`."""

from typing import Any


class RpcClient:
    """Wrapper around RPC communication."""

    def __init__(self, url: str) -> None:
        self.url = url

    def send_request(self, method: str, params: Any) -> Any:
        """Send an RPC request and return the response."""
        raise NotImplementedError


def mock_sender_for_cli() -> None:
    """Return a mock sender similar to ``mock_sender_for_cli`` in Rust."""

