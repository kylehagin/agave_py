"""Simplified loader for BPF like programs.

The original crate contains a full blown runtime and a suite of benchmarks.  In
this stub we only keep enough logic to register binary blobs alongside callable
Python functions.
"""

from __future__ import annotations

from typing import Dict

from ..program_runtime import Program, Runtime


class BPFLoader(Runtime):
    """Runtime that loads programs from raw bytes."""

    def __init__(self) -> None:
        super().__init__()
        self._binaries: Dict[str, bytes] = {}

    def load_program(self, name: str, binary: bytes, func) -> None:
        self._binaries[name] = binary
        self.register(name, Program(func))


__all__ = ["BPFLoader"]

