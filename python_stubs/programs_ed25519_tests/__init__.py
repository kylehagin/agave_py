"""Light-weight Ed25519 test utilities.

The actual Rust crate performs cryptographic signature verification tests.  Here
we use a very small helper that emulates signing via ``sha512`` so that unit
tests can verify control flow without additional dependencies.
"""

from __future__ import annotations

import hashlib
import unittest


def _fake_sign(message: bytes) -> bytes:
    """Return a fake signature using SHA-512."""

    return hashlib.sha512(message).digest()[:64]


class Ed25519TestCase(unittest.TestCase):
    """Base class for Ed25519 related tests."""

    def assertSignatureValid(self, message: bytes, signature: bytes) -> None:
        self.assertEqual(_fake_sign(message), signature)


__all__ = ["Ed25519TestCase", "_fake_sign"]

