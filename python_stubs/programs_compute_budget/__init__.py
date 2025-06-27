"""Simple compute budget tracker.

The Rust counterpart defines an on-chain program; this stub merely tracks usage
locally and can be exercised from unit tests.
"""

from __future__ import annotations


class ComputeBudget:
    """Keeps track of used compute units."""

    def __init__(self, limit: int):
        self.limit = limit
        self.used = 0

    def consume(self, amount: int) -> None:
        if self.used + amount > self.limit:
            raise RuntimeError("compute budget exceeded")
        self.used += amount

    def remaining(self) -> int:
        return self.limit - self.used


__all__ = ["ComputeBudget"]

