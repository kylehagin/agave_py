"""Minimal program runtime environment.

The real ``program-runtime`` crate provides execution facilities for on-chain
programs.  Here we implement a small in-memory dispatcher that can be used from
Python unit tests.
"""

from __future__ import annotations

from typing import Callable, Dict, Any


class Program:
    """Represents a small executable program."""

    def __init__(self, func: Callable[[Any], Any]):
        self.func = func

    def run(self, arg: Any) -> Any:
        return self.func(arg)


class Runtime:
    """Simple registry for :class:`Program` objects."""

    def __init__(self) -> None:
        self._programs: Dict[str, Program] = {}

    def register(self, name: str, program: Program) -> None:
        self._programs[name] = program

    def invoke(self, name: str, arg: Any) -> Any:
        if name not in self._programs:
            raise KeyError(f"Program '{name}' not found")
        return self._programs[name].run(arg)


__all__ = ["Program", "Runtime"]

