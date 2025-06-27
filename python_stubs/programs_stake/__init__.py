"""Simplified stake program.

The real program handles delegation and rewards in the Solana runtime.  The
implementation here is intentionally tiny and intended purely for unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StakeAccount:
    owner: str
    balance: int


class StakeProgram:
    def __init__(self) -> None:
        self.accounts: dict[str, StakeAccount] = {}

    def create_account(self, name: str, owner: str, balance: int) -> None:
        self.accounts[name] = StakeAccount(owner, balance)

    def delegate(self, name: str, validator: str) -> None:
        if name not in self.accounts:
            raise KeyError("Unknown stake account")
        self.accounts[name].owner = validator


__all__ = ["StakeAccount", "StakeProgram"]

