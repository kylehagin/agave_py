"""Simplified Proof of History implementation.

This module provides a small Python representation of the ``poh`` crate.  The
real crate implements Solana's Proof of History mechanism.  The code below is
not a full port; it merely offers a digest based chain so that other Python
components can experiment with a PoH like API.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class ProofOfHistory:
    """Minimal PoH recorder.

    Parameters
    ----------
    seed : bytes, optional
        Initial seed for the chain.  Defaults to ``b""``.
    """

    seed: bytes = b""
    _chain: List[bytes] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._last_hash = hashlib.sha256(self.seed).digest()

    @property
    def last_hash(self) -> bytes:
        """Return the most recently generated hash."""

        return self._last_hash

    def record(self, data: bytes) -> bytes:
        """Record ``data`` into the PoH chain.

        Parameters
        ----------
        data : bytes
            Arbitrary binary data to record.

        Returns
        -------
        bytes
            The newly computed hash.
        """

        digest = hashlib.sha256(self._last_hash + data).digest()
        self._chain.append(digest)
        self._last_hash = digest
        return digest

    def verify(self, data_stream: Iterable[bytes]) -> bool:
        """Verify a stream of data matches the recorded chain."""

        last = hashlib.sha256(self.seed).digest()
        for expected, data in zip(self._chain, data_stream):
            last = hashlib.sha256(last + data).digest()
            if last != expected:
                return False
        return True


__all__ = ["ProofOfHistory"]

