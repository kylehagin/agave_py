"""Test helpers for the :mod:`programs_stake` module.

The original crate defines unit tests for the Solana stake program.  Subclass
:class:`StakeProgramTestCase` to write equivalent Python tests.
"""

from __future__ import annotations

import unittest

from ..programs_stake import StakeProgram


class StakeProgramTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.program = StakeProgram()


__all__ = ["StakeProgramTestCase"]

