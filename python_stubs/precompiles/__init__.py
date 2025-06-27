"""Basic precompile registry used during testing.

The Rust crate includes micro-benchmarks for various precompile utilities.
Benchmarking can be replicated in Python by timing calls to the registry.
"""

from __future__ import annotations

from typing import Callable, Dict


class PrecompileRegistry:
    """Registry mapping names to Python callables."""

    def __init__(self) -> None:
        self._registry: Dict[str, Callable[..., object]] = {}

    def register(self, name: str, func: Callable[..., object]) -> None:
        self._registry[name] = func

    def run(self, name: str, *args, **kwargs) -> object:
        if name not in self._registry:
            raise KeyError(f"Unknown precompile: {name}")
        return self._registry[name](*args, **kwargs)


__all__ = ["PrecompileRegistry"]

