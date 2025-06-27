"""Simplified Poseidon hash implementation."""

from __future__ import annotations

import hashlib
from typing import Iterable


def poseidon_hash(inputs: Iterable[bytes]) -> bytes:
    """Compute a simple "Poseidon" style hash.

    This is **not** the real Poseidon hash function; instead we simply
    concatenate the inputs and feed them through SHA-256.  The real crate uses a
    highly optimised cryptographic permutation which is outside the scope of
    this repository.
    """

    hasher = hashlib.sha256()
    for item in inputs:
        hasher.update(item)
    return hasher.digest()


__all__ = ["poseidon_hash"]

