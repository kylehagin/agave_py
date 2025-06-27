"""Python stubs mirroring the `cli-config` crate."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration file structure used by the CLI."""

    json_rpc_url: str
    keypair_path: str

    @classmethod
    def load(cls, path: str) -> "Config":  # noqa: D401
        """Load configuration from ``path``."""
        raise NotImplementedError

    def save(self, path: str) -> None:  # noqa: D401
        """Save configuration to ``path``."""


def load_config_file(path: str):
    """Load a YAML config file, mirroring `load_config_file` from Rust."""


def save_config_file(config, path: str) -> None:
    """Write a YAML config file, mirroring `save_config_file` from Rust."""

