"""Python stub for the ``accounts-cluster-bench`` tool.

The original utility performs cluster based benchmarking by sending RPC calls
to a validator.  The Python implementation provides small helper functions used
by other stubs.
"""

from __future__ import annotations

import time
from typing import Any, Optional

MAX_RPC_CALL_RETRIES = 5


def poll_slot_height(client: Any, retries: int = MAX_RPC_CALL_RETRIES) -> int:
    """Poll ``client`` until a slot height is returned or ``retries`` expire."""

    while retries > 0:
        try:
            return client.get_slot_with_commitment("confirmed")  # type: ignore
        except Exception:  # pragma: no cover - best effort stub
            retries -= 1
            time.sleep(0.1)
    raise RuntimeError("failed to get slot height")


def poll_get_latest_blockhash(client: Any, retries: int = MAX_RPC_CALL_RETRIES) -> Optional[str]:
    """Poll ``client`` for the most recent blockhash."""

    while retries > 0:
        try:
            return client.get_latest_blockhash()  # type: ignore
        except Exception:
            retries -= 1
            time.sleep(0.1)
    return None


def poll_get_fee_for_message(client: Any, message: Any, retries: int = MAX_RPC_CALL_RETRIES) -> tuple[Optional[int], Any]:
    """Poll ``client`` for the fee of ``message`` and return the blockhash used."""

    while retries > 0:
        try:
            fee = client.get_fee_for_message(message)  # type: ignore
            return fee, getattr(message, "recent_blockhash", None)
        except Exception:
            retries -= 1
            time.sleep(0.1)
    raise RuntimeError("failed to get fee for message")

