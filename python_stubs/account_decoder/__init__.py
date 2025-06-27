"""Python stub for crate ``account-decoder``.

This module exposes a tiny subset of the helpers provided by the real Rust
crate.  The Rust crate is responsible for converting on-chain account data into
a JSON representation returned by RPC calls.  Only the most commonly referenced
types and helper functions are mirrored here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from account_decoder_client_types import (
    ParsedAccount,
    UiAccount,
    UiAccountData,
    UiAccountEncoding,
    UiDataSliceConfig,
)

StringAmount = str
StringDecimals = str

MAX_BASE58_BYTES: int = 128


def _slice_data(data: bytes, data_slice_config: Optional[UiDataSliceConfig]) -> bytes:
    """Return ``data`` sliced according to ``data_slice_config``."""

    if data_slice_config is None:
        return data
    offset, length = data_slice_config.offset, data_slice_config.length
    if offset >= len(data):
        return b""
    return data[offset : offset + length]


def encode_ui_account(
    pubkey: str,
    account: "ReadableAccount",
    encoding: UiAccountEncoding,
    additional_data: Optional[ParsedAccount] = None,
    data_slice_config: Optional[UiDataSliceConfig] = None,
) -> UiAccount:
    """Encode an account into :class:`UiAccount`.

    The Python version performs no real parsing and simply returns the sliced
    account data encoded in base64 or base58 depending on ``encoding``.
    """

    data = _slice_data(account.data, data_slice_config)
    if encoding in {UiAccountEncoding.BINARY, UiAccountEncoding.BASE58}:
        import base58

        blob = base58.b58encode(data).decode("ascii")
        ui_data = UiAccountData(blob, encoding)
    else:
        import base64

        blob = base64.b64encode(data).decode("ascii")
        ui_data = UiAccountData(blob, encoding)

    return UiAccount(
        lamports=account.lamports,
        data=ui_data,
        owner=account.owner,
        executable=account.executable,
        rent_epoch=account.rent_epoch,
        space=len(account.data),
    )


@dataclass
class UiFeeCalculator:
    """Simplified version of the Rust ``UiFeeCalculator`` struct."""

    lamports_per_signature: StringAmount = "0"

