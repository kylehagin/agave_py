"""Python adaptation of the ``banks-interface`` crate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional


class TransactionConfirmationStatus(Enum):
    PROCESSED = "processed"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"


@dataclass
class TransactionStatus:
    slot: int
    confirmations: Optional[int]
    err: Optional[str]
    confirmation_status: Optional[TransactionConfirmationStatus]


@dataclass
class TransactionSimulationDetails:
    logs: List[str]
    units_consumed: int
    loaded_accounts_data_size: int
    return_data: Optional[Any]
    inner_instructions: Optional[Any]


@dataclass
class TransactionMetadata:
    log_messages: List[str]
    compute_units_consumed: int
    return_data: Optional[Any]


@dataclass
class BanksTransactionResultWithSimulation:
    result: Optional[Any]
    simulation_details: Optional[TransactionSimulationDetails]


@dataclass
class BanksTransactionResultWithMetadata:
    result: Any
    metadata: Optional[TransactionMetadata]


class Banks:
    """Interface describing the RPC methods provided by ``banks-server``."""

    async def send_transaction_with_context(self, transaction: Any) -> None:
        raise NotImplementedError

