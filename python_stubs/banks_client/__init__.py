"""Simplified Python port of the ``banks-client`` crate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


class BanksClientError(Exception):
    """Error type used by :class:`BanksClient`."""


@dataclass
class TransactionStatus:
    """Minimal stand in for ``TransactionStatus``."""

    slot: int
    err: Optional[str] = None


class BanksClient:
    """Very small subset of the async client used in tests."""

    def __init__(self, transport: Any) -> None:  # pragma: no cover - placeholder
        self._transport = transport

    def send_transaction(self, transaction: Any) -> None:
        """Pretend to send ``transaction`` to the server."""

        raise BanksClientError("send_transaction not implemented")

    def get_transaction_status(self, signature: str) -> TransactionStatus:
        """Fetch the status for ``signature``."""

        raise BanksClientError("get_transaction_status not implemented")

