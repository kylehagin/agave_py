"""High level representation of a transaction and its message."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class TransactionView:
    message: str
    signatures: List[str]


__all__ = ["TransactionView"]

