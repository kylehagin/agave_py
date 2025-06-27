"""Python helpers mirroring the `clap-v3-utils` crate."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ArgConstant:
    """Represents metadata for a clap argument."""

    long: str
    name: str
    help: str


class DisplayError(Exception):
    """Error wrapper providing ``Display`` semantics."""

    def __init__(self, inner: Exception) -> None:
        super().__init__(str(inner))
        self.inner = inner


def hidden_unless_forced() -> bool:
    """Return ``True`` if hidden arguments remain hidden."""
    return True

