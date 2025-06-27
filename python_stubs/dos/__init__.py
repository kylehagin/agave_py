"""Simplified translation of the ``dos`` crate CLI types."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class Mode(Enum):
    """Interface used for DoS."""

    GOSSIP = auto()
    TVU = auto()
    TPU = auto()
    TPU_FORWARDS = auto()
    REPAIR = auto()
    SERVE_REPAIR = auto()
    RPC = auto()


class DataType(Enum):
    REPAIR_HIGHEST = auto()
    REPAIR_SHRED = auto()
    REPAIR_ORPHAN = auto()
    RANDOM = auto()
    GET_ACCOUNT_INFO = auto()
    GET_PROGRAM_ACCOUNTS = auto()
    TRANSACTION = auto()


class TransactionType(Enum):
    TRANSFER = auto()
    ACCOUNT_CREATION = auto()


@dataclass
class TransactionParams:
    num_signatures: Optional[int] = None
    valid_blockhash: bool = False
    valid_signatures: bool = False
    unique_transactions: bool = False
    transaction_type: Optional[TransactionType] = None
    num_instructions: Optional[int] = None


@dataclass
class DosClientParameters:
    mode: Mode
    data_type: DataType
    entrypoint_addr: str = "127.0.0.1:8001"
    data_size: int = 128
    data_input: Optional[str] = None
    skip_gossip: bool = False
    shred_version: Optional[int] = None
    allow_private_addr: bool = False
    num_gen_threads: int = 1
    transaction_params: TransactionParams = TransactionParams()
    tpu_use_quic: bool = False
    send_batch_size: int = 16384


def build_cli_parameters() -> DosClientParameters:
    """Return parameters parsed from ``sys.argv``.

    This implementation is vastly simplified and accepts no arguments.
    It merely returns the defaults used for testing.
    """

    # TODO: translate the real clap based argument parser
    return DosClientParameters(mode=Mode.TPU, data_type=DataType.TRANSACTION)

