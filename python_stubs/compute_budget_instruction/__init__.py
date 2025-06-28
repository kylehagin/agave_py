"""Python utilities mirroring the `compute-budget-instruction` crate."""

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass
class ComputeBudgetInstructionDetails:
    """Details extracted from a set of compute budget instructions."""

    requested_compute_unit_limit: Tuple[int, int] | None = None
    requested_compute_unit_price: Tuple[int, int] | None = None

    @classmethod
    def try_from(cls, instructions: Iterable[Tuple[str, bytes]]):  # noqa: D401
        """Construct from an iterator of instructions."""
        details = cls()
        for idx, (program, data) in enumerate(instructions):
            if program != "compute_budget":
                continue
            if not data:
                raise ValueError("Invalid instruction data")
            tag = data[0]
            if tag == 1:  # SetComputeUnitLimit
                if len(data) != 5:
                    raise ValueError("Invalid compute unit limit data")
                if details.requested_compute_unit_limit is not None:
                    raise ValueError("Duplicate compute unit limit request")
                value = int.from_bytes(data[1:], "little")
                details.requested_compute_unit_limit = (idx, value)
            elif tag == 2:  # SetComputeUnitPrice
                if len(data) != 9:
                    raise ValueError("Invalid compute unit price data")
                if details.requested_compute_unit_price is not None:
                    raise ValueError("Duplicate compute unit price request")
                value = int.from_bytes(data[1:], "little")
                details.requested_compute_unit_price = (idx, value)
            else:
                raise ValueError("Unsupported compute budget instruction")
        return details

    def sanitize_and_convert_to_compute_budget_limits(self, feature_set) -> object:
        """Sanitize and convert to ``ComputeBudgetLimits``."""
        from ..compute_budget import ComputeBudgetLimits

        cu_limit = 0
        cu_price = 0

        if self.requested_compute_unit_limit is not None:
            _, limit = self.requested_compute_unit_limit
            if limit < 0:
                raise ValueError("Invalid compute unit limit")
            cu_limit = limit

        if self.requested_compute_unit_price is not None:
            _, price = self.requested_compute_unit_price
            if price < 0:
                raise ValueError("Invalid compute unit price")
            cu_price = price

        return ComputeBudgetLimits(
            updated_heap_bytes=0,
            compute_unit_limit=cu_limit,
            compute_unit_price=cu_price,
        )

