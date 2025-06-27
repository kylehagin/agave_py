"""Interfaces for building Geyser plugins."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ReplicaAccountInfo:
    pubkey: bytes
    lamports: int
    owner: bytes
    executable: bool
    rent_epoch: int
    data: bytes
    write_version: int
    txn_signature: Optional[bytes] = None


@dataclass
class ReplicaTransactionInfo:
    signature: bytes
    is_vote: bool
    transaction: Any
    transaction_status_meta: Any
    index: int = 0


class SlotStatus:
    PROCESSED = "processed"
    ROOTED = "rooted"
    CONFIRMED = "confirmed"


class GeyserPlugin:
    """Base class for plugins."""

    def name(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    # The following callbacks do nothing by default.  Plugins can override them.
    def on_load(self, config_file: str, is_reload: bool) -> None:  # pragma: no cover
        pass

    def on_unload(self) -> None:  # pragma: no cover
        pass

    def update_account(
        self, account: ReplicaAccountInfo, slot: int, is_startup: bool
    ) -> None:  # pragma: no cover
        pass

    def notify_transaction(self, transaction: ReplicaTransactionInfo, slot: int) -> None:
        pass

