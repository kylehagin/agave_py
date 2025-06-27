"""Helpers for deciding whether to record transaction metrics."""

from __future__ import annotations

import os
import random

SIGNATURE_BYTES = 64
_TXN_MASK = random.randrange(0, 4096)


def should_track_transaction(signature: bytes) -> bool:
    if len(signature) < SIGNATURE_BYTES:
        return False
    match_portion = int.from_bytes(signature[61:63], "little") >> 4
    return match_portion == _TXN_MASK


__all__ = ["should_track_transaction", "SIGNATURE_BYTES"]

