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
        raise NotImplementedError

    def sanitize_and_convert_to_compute_budget_limits(self, feature_set) -> object:
        """Sanitize and convert to ``ComputeBudgetLimits``."""
        raise NotImplementedError

