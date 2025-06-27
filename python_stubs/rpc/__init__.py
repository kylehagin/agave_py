"""Placeholder API for the `rpc` crate."""

from dataclasses import dataclass
from typing import Any


@dataclass
class JsonRpcConfig:
    enable_rpc_transaction_history: bool = False


@dataclass
class RpcBigtableConfig:
    enable_bigtable_ledger_storage: bool = False


class JsonRpcRequestProcessor:
    """Simplified request processor."""

    def __init__(self, config: JsonRpcConfig | None = None) -> None:
        self.config = config or JsonRpcConfig()

    def process_request(self, request: Any) -> Any:
        """Process an RPC request (no-op)."""
        return None
