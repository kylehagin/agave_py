"""Utilities for building transactions used by :mod:`runtime`.

This module only contains a dataclass representing a transaction.  The real
Rust crate has additional serialization and verification logic which are not
reproduced here.
"""

from dataclasses import dataclass


@dataclass
class RuntimeTransaction:
    sender: str
    receiver: str
    amount: int

    def to_dict(self) -> dict:
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict) -> "RuntimeTransaction":
        return cls(data["sender"], data["receiver"], int(data["amount"]))


__all__ = ["RuntimeTransaction"]
