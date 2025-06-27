"""Utility functions for zero-knowledge key generation."""

from __future__ import annotations

import secrets
from dataclasses import dataclass


@dataclass
class ZkKeypair:
    private: bytes
    public: bytes


def generate_keypair() -> ZkKeypair:
    """Generate a random keypair.

    Real implementations would use an actual zero-knowledge friendly curve.
    Here we simply generate two random 32 byte values.
    """

    private = secrets.token_bytes(32)
    public = secrets.token_bytes(32)
    return ZkKeypair(private=private, public=public)


__all__ = ["ZkKeypair", "generate_keypair"]

