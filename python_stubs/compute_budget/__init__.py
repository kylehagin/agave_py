"""Python representation of the `compute-budget` crate."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ComputeBudget:
    """Compute budget parameters."""

    compute_unit_limit: int
    log_64_units: int = 0

    def to_budget(self) -> object:
        """Convert to a Rust-like budget object."""
        raise NotImplementedError


@dataclass
class ComputeBudgetLimits:
    """Limits used when creating a compute budget."""

    updated_heap_bytes: int
    compute_unit_limit: int
    compute_unit_price: int

    def get_prioritization_fee(self) -> int:
        """Return the prioritization fee."""
        return 0

