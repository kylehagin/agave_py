"""Python stub for crate ``account-decoder-client-types``.

This module provides Python representations of the types used by the
``account-decoder`` crate.  The real crate defines a large collection of
structures that describe decoded account state returned from Solana RPC
endpoints.  Only a very small portion is reproduced here to satisfy type
checking of the Python bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class UiAccountEncoding(Enum):
    """Enum describing how account data is encoded."""

    BINARY = "binary"
    BASE58 = "base58"
    BASE64 = "base64"
    JSON_PARSED = "jsonParsed"
    BASE64_ZSTD = "base64+zstd"


@dataclass
class UiDataSliceConfig:
    """Configuration describing a slice of account data."""

    offset: int
    length: int


class UiAccountData:
    """Container for account data returned by RPC calls."""

    def __init__(self, raw_data: Any, encoding: UiAccountEncoding) -> None:
        self.raw_data = raw_data
        self.encoding = encoding

    def decode(self) -> Optional[bytes]:
        """Return decoded binary data if possible."""

        if self.encoding in {UiAccountEncoding.BASE64, UiAccountEncoding.BASE64_ZSTD}:
            import base64

            try:
                return base64.b64decode(self.raw_data)
            except Exception:
                return None
        if self.encoding == UiAccountEncoding.BASE58:
            try:
                import base58

                return base58.b58decode(self.raw_data)
            except Exception:
                return None
        return None


@dataclass
class UiAccount:
    """Simplified representation of a Solana account."""

    lamports: int
    data: UiAccountData
    owner: str
    executable: bool
    rent_epoch: int
    space: Optional[int] = None


@dataclass
class ParsedAccount:
    """Result of parsing account data on the Rust side."""

    program: str
    parsed: Any
    space: int


@dataclass
class UiTokenAmount:
    """Representation of a token amount with decimal support."""

    amount: str
    decimals: int
    ui_amount: Optional[float] = None
    ui_amount_string: str = ""

    def real_number_string(self) -> str:
        """Return the amount as a string with decimals."""

        return real_number_string(int(self.amount), self.decimals)

    def real_number_string_trimmed(self) -> str:
        """Return a trimmed version of :meth:`real_number_string`."""

        if self.ui_amount_string:
            return self.ui_amount_string
        return real_number_string_trimmed(int(self.amount), self.decimals)


def real_number_string(amount: int, decimals: int) -> str:
    """Return ``amount`` formatted using ``decimals`` decimal places."""

    if decimals > 0:
        s = f"{amount:0{decimals + 1}d}"
        return f"{s[:-decimals]}.{s[-decimals:]}"
    return str(amount)


def real_number_string_trimmed(amount: int, decimals: int) -> str:
    """Return a trimmed decimal string without trailing zeros."""

    s = real_number_string(amount, decimals)
    if decimals > 0:
        s = s.rstrip("0").rstrip(".")
    return s

