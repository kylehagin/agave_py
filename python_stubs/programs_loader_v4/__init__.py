"""Minimal representation of loader version 4.

The real loader is responsible for deploying on-chain programs.  This stub only
stores the binaries that were "loaded" for use in unit tests.
"""

from __future__ import annotations


class LoaderV4:
    """Loads programs using the V4 protocol."""

    def __init__(self) -> None:
        self.loaded = {}

    def load(self, name: str, binary: bytes) -> None:
        self.loaded[name] = binary


__all__ = ["LoaderV4"]

