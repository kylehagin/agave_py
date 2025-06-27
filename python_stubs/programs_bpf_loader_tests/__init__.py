"""Test helpers for :mod:`programs_bpf_loader`.

The real crate contains a collection of integration tests.  This module merely
provides a :class:`BPFLoaderTestCase` base class that can be extended to emulate
similar behaviour in Python.
"""

from __future__ import annotations

import unittest

from ..programs_bpf_loader import BPFLoader


class BPFLoaderTestCase(unittest.TestCase):
    """Base test case for BPF loader tests."""

    def setUp(self) -> None:
        self.loader = BPFLoader()


__all__ = ["BPFLoaderTestCase"]

