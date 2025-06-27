"""Fee calculation helpers."""

from dataclasses import dataclass


@dataclass
class FeeFeatures:
    enable_secp256r1_precompile: bool = False


def calculate_fee(
    message: "Message",
    zero_fees_for_test: bool,
    lamports_per_signature: int,
    prioritization_fee: int,
    fee_features: FeeFeatures,
) -> int:
    """Return the total fee for a message.

    The real implementation accounts for additional signature types and
    prioritization fees.  Here we simply multiply the number of signatures
    by ``lamports_per_signature``.
    """

    if zero_fees_for_test:
        return 0

    sigs = getattr(message, "num_transaction_signatures", lambda: 0)()
    return sigs * lamports_per_signature + prioritization_fee


# TODO: model FeeDetails when needed.

