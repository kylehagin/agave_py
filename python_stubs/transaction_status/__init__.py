"""Utilities for representing transaction status information."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TransactionDetails(Enum):
    FULL = auto()
    SIGNATURES = auto()
    NONE = auto()


@dataclass
class TransactionStatus:
    signature: str
    slot: int
    err: bool = False


__all__ = ["TransactionStatus", "TransactionDetails"]

