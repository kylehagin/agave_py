"""Collect rent from accounts over time."""

from dataclasses import dataclass


@dataclass
class RentCollector:
    lamports_per_slot: int

    def collect(self, balance: int, slots: int) -> int:
        rent = self.lamports_per_slot * slots
        return max(balance - rent, 0)


__all__ = ["RentCollector"]
