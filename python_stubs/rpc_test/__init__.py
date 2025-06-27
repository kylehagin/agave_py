"""Simplified utilities for testing RPC components.

This module emulates a very small portion of the Rust `rpc-test` crate.  It
provides a :class:`MockRPC` object that can register Python callables as RPC
methods and invoke them synchronously.  Network and concurrency behaviour of the
original crate are not implemented; this is purely an in‑process dispatcher used
for unit tests.
"""

from typing import Any, Callable, Dict


class MockRPC:
    """A tiny in-memory RPC dispatcher used for tests."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register(self, method: str, func: Callable[..., Any]) -> None:
        """Register ``func`` to be called when ``method`` is invoked."""

        self._handlers[method] = func

    def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke a registered RPC method.

        Raises ``ValueError`` if the method is unknown.
        """

        if method not in self._handlers:
            raise ValueError(f"Unknown RPC method: {method}")
        return self._handlers[method](*args, **kwargs)


__all__ = ["MockRPC"]
