"""Simplified stake account management.

The original Rust crate deals with Solana's stake program.  Here we implement a
very small portion that keeps track of an owner and their staked amount.
"""

from dataclasses import dataclass


@dataclass
class StakeAccount:
    owner: str
    stake: int = 0

    def delegate(self, amount: int) -> None:
        self.stake += amount

    def withdraw(self, amount: int) -> bool:
        if amount > self.stake:
            return False
        self.stake -= amount
        return True


__all__ = ["StakeAccount"]
