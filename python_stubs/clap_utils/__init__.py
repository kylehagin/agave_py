"""Python helpers corresponding to the Rust crate `clap-utils`."""

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ArgConstant:
    """Represents a constant command line argument."""

    long: str
    name: str
    help: str


class DisplayError(Exception):
    """Error wrapper mirroring ``DisplayError`` from Rust."""

    def __init__(self, inner: Exception) -> None:
        super().__init__(str(inner))
        self.inner = inner


def hidden_unless_forced() -> bool:
    """Return ``True`` if arguments marked hidden should remain hidden."""
    return True


def compute_unit_price_arg() -> Any:
    """Return the argument definition for compute unit price."""


def compute_unit_limit_arg() -> Any:
    """Return the argument definition for compute unit limit."""

