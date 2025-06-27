"""Python translation of the `programs/system` crate."""

from enum import Enum
from typing import Set, Any

DEFAULT_COMPUTE_UNITS: int = 150

class SystemAccountKind(Enum):
    """Placeholder for `SystemAccountKind`."""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"


def id() -> str:
    """Return the static program id for the system program."""
    return "System111111111111111111111111111111111111"


def get_system_account_kind(account: Any) -> SystemAccountKind:
    """Return the `SystemAccountKind` for the given account.

    This stub always returns :class:`SystemAccountKind.UNINITIALIZED`.
    """
    return SystemAccountKind.UNINITIALIZED


def advance_nonce_account(account: Any, signers: Set[str], invoke_context: Any | None = None) -> None:
    """Advance a nonce account. This is a no-op placeholder."""
    pass
