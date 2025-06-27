"""Utilities mirroring the ``program-test`` crate.

The Rust crate offers a high level testing framework for on-chain programs.  In
this simplified Python version tests can inherit from :class:`ProgramTestCase`
to register and invoke small ``Program`` objects.
"""

from __future__ import annotations

import unittest

from ..program_runtime import Program, Runtime


class ProgramTestCase(unittest.TestCase):
    """Base class for program tests."""

    def setUp(self) -> None:  # noqa: D401 - short description
        self.runtime = Runtime()

    def register_program(self, name: str, func) -> None:
        self.runtime.register(name, Program(func))

    def invoke(self, name: str, arg):
        return self.runtime.invoke(name, arg)


__all__ = ["ProgramTestCase"]

