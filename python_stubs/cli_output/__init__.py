"""Python API for the ``cli-output`` crate."""

from typing import Any


class QuietDisplay:
    """Trait used for quiet display output."""

    def write_str(self, w: Any) -> None:  # noqa: D401
        """Write the string representation to ``w``."""


class VerboseDisplay:
    """Trait used for verbose display output."""

    def write_str(self, w: Any) -> None:  # noqa: D401
        """Write the string representation to ``w``."""


def build_balance_message(lamports: int, use_lamports_unit: bool, show_unit: bool) -> str:
    """Create a balance message similar to the Rust implementation."""
    return ""

