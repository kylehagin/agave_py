"""Python interface mirroring the Rust crate `builtins`."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CoreBpfMigrationConfig:
    """Configuration describing migration of a builtin program."""

    source_buffer_address: str
    upgrade_authority_address: Optional[str]
    feature_id: str
    verified_build_hash: Optional[str]
    migration_target: str
    datapoint_name: str


@dataclass
class BuiltinPrototype:
    """Represents a builtin program definition."""

    name: str
    program_id: str
    entrypoint: str
    core_bpf_migration_config: Optional[CoreBpfMigrationConfig] = None
    enable_feature_id: Optional[str] = None


@dataclass
class StatelessBuiltinPrototype(BuiltinPrototype):
    """Prototype for stateless builtin programs."""


BUILTINS: List[BuiltinPrototype] = []
"""List of builtin program prototypes defined by the Rust crate."""

STATELESS_BUILTINS: List[StatelessBuiltinPrototype] = []
"""List of stateless builtin prototypes defined by the Rust crate."""

