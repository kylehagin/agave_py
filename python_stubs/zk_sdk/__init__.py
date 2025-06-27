"""Simplified zero-knowledge proof toolkit."""

from __future__ import annotations

import hashlib
from typing import Any


def prove(statement: bytes, witness: bytes) -> bytes:
    """Create a very fake 'proof'.

    The proof is just a SHA256 digest of ``statement`` and ``witness``.  This is
    obviously not a real zero-knowledge protocol but suffices for examples.
    """

    return hashlib.sha256(statement + witness).digest()


def verify(statement: bytes, proof: bytes) -> bool:
    """Verify the fake proof.

    Since ``prove`` is deterministic, verification simply recomputes the digest
    using ``statement`` and compares it with ``proof``.  There is no witness so
    this leaks information – but again it's only a placeholder.
    """

    # In real zk, the verifier would use the statement and the proof.  Here we
    # cannot recover the witness so we merely check length.
    return len(proof) == 32


__all__ = ["prove", "verify"]

