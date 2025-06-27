"""Python bindings for the Rust crate `bloom`.

This module provides lightweight Python representations of the data
structures exposed by the Rust implementation.  The interfaces mirror the
original APIs but contain no functionality.
"""

from dataclasses import dataclass
from typing import Iterable


class BloomHashIndex:
    """Trait implemented by types that can produce stable hashes.

    This mirrors the ``BloomHashIndex`` trait from the Rust crate.
    """

    def hash_at_index(self, hash_index: int) -> int:
        """Return a 64‑bit hash for ``hash_index``."""
        raise NotImplementedError


@dataclass
class Bloom:
    """Simplified representation of ``Bloom<T>`` from the Rust crate."""

    num_bits: int
    keys: list[int]

    def add(self, key: BloomHashIndex) -> None:  # noqa: D401
        """Add ``key`` to the Bloom filter."""

    def contains(self, key: BloomHashIndex) -> bool:  # noqa: D401
        """Return ``True`` if ``key`` may be in the filter."""
        return False

    def clear(self) -> None:  # noqa: D401
        """Reset all bits."""


class ConcurrentBloom(Bloom):
    """Placeholder for ``ConcurrentBloom`` in the Rust crate."""

    pass


class ConcurrentBloomInterval(ConcurrentBloom):
    """Wrapper providing periodic clearing of a ``ConcurrentBloom``."""

    def maybe_reset(self, reset_interval_ms: int) -> None:  # noqa: D401
        """Reset the filter if ``reset_interval_ms`` has elapsed."""

