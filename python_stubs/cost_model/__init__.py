"""Python translation of the Rust ``cost-model`` crate.

Only the most important structures are represented.  The real crate
contains far more logic around transaction cost calculations.  Most of
those details are omitted here.
"""

from dataclasses import dataclass
from typing import Iterator, Tuple


@dataclass
class UsageCostDetails:
    """Simplified representation of a transaction cost."""

    signature_cost: int
    write_lock_cost: int
    data_bytes_cost: int
    programs_execution_cost: int
    loaded_accounts_data_size_cost: int
    allocated_accounts_data_size: int


class CostModel:
    """Utility for estimating transaction cost."""

    @staticmethod
    def calculate_cost(
        tx: "Transaction", feature_set: "FeatureSet"
    ) -> UsageCostDetails:
        """Return an estimated cost for ``tx``.

        This is only a placeholder implementation.  The real logic
        accounts for many details from ``feature_set`` and the
        transaction contents.
        """

        # TODO: translate fee structure and compute budget behaviour.
        sig_cost = len(getattr(tx, "signatures", [])) * 1
        write_lock_cost = getattr(tx, "num_write_locks", lambda: 0)()
        return UsageCostDetails(
            signature_cost=sig_cost,
            write_lock_cost=write_lock_cost,
            data_bytes_cost=len(getattr(tx, "data", b"")),
            programs_execution_cost=0,
            loaded_accounts_data_size_cost=0,
            allocated_accounts_data_size=0,
        )


# TODO: add FeatureSet, Transaction and other related types when
# additional crates are translated.

