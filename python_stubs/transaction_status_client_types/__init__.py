"""Types shared by transaction status RPC clients."""

from __future__ import annotations

from enum import Enum, auto


class UiTransactionEncoding(Enum):
    BASE64 = auto()
    BASE58 = auto()
    JSON = auto()


__all__ = ["UiTransactionEncoding"]

