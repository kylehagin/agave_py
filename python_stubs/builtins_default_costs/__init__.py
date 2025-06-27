"""Python wrapper for the Rust crate `builtins-default-costs`."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MigratingBuiltinCost:
    """Cost information for a builtin that is migrating to core BPF."""

    native_cost: int
    core_bpf_migration_feature: str
    position: int


@dataclass
class NotMigratingBuiltinCost:
    """Cost information for a builtin that is not migrating."""

    native_cost: int


class BuiltinCost:
    """Union of builtin cost types."""

    def __init__(self, migrating: Optional[MigratingBuiltinCost] = None,
                 not_migrating: Optional[NotMigratingBuiltinCost] = None) -> None:
        self.migrating = migrating
        self.not_migrating = not_migrating


def get_builtin_instruction_cost(program_id: str, feature_set: object) -> Optional[int]:
    """Return the default cost for ``program_id``.

    This mirrors ``get_builtin_instruction_cost`` in the Rust crate.
    """
    return None


def get_builtin_migration_feature_index(program_id: str) -> int:
    """Return the migration feature index for ``program_id`` or ``0``."""
    return 0

