"""Common types for RPC client requests and responses."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RpcRequest:
    method: str
    params: Any


@dataclass
class RpcResponse:
    result: Any
    error: Any | None = None
