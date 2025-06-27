"""Helper functions for serialising objects to simple dictionaries.

The Rust crate contains build scripts that generate protobuf types.  In this
Python stub we merely convert dataclasses or objects with ``__dict__`` into a
dictionary so that they can be stored in :mod:`storage_bigtable`.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict


def build_proto(obj: Any) -> Dict[str, Any]:
    """Return a dictionary representation of ``obj``."""

    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise TypeError("Object is not serialisable")


__all__ = ["build_proto"]
