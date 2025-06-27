"""Simplified bindings for the ``curves/curve25519`` crate."""

from dataclasses import dataclass
from typing import Iterable


@dataclass
class PodEdwardsPoint:
    """Wrapper around 32 bytes representing a curve point."""

    data: bytes

    def validate(self) -> bool:
        """Return ``True`` if the point is on the curve."""

        # TODO: call into actual curve25519 library for validation
        return len(self.data) == 32


def add_edwards(left: PodEdwardsPoint, right: PodEdwardsPoint) -> PodEdwardsPoint:
    """Add two points together.

    This function only checks lengths of the inputs.  Real elliptic curve math
    is not implemented here.
    """

    if len(left.data) != 32 or len(right.data) != 32:
        raise ValueError("invalid point length")
    # TODO: perform real point addition
    return PodEdwardsPoint(bytes(32))


def multiscalar_multiply(
    scalars: Iterable[bytes], points: Iterable[PodEdwardsPoint]
) -> PodEdwardsPoint:
    """Placeholder for multi-scalar multiplication."""

    # TODO: implement real MSM via curve library
    return PodEdwardsPoint(bytes(32))

