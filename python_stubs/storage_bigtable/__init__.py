"""In-memory Bigtable style key/value store.

This module offers a tiny stand-in for the real Bigtable integration used in
Solana.  Data is stored in nested dictionaries and is lost when the program
exits.
"""

from typing import Any, Dict


class BigtableStorage:
    """A very small table store organised by table name."""

    def __init__(self) -> None:
        self._tables: Dict[str, Dict[str, Any]] = {}

    def put(self, table: str, key: str, value: Any) -> None:
        self._tables.setdefault(table, {})[key] = value

    def get(self, table: str, key: str) -> Any:
        return self._tables.get(table, {}).get(key)


__all__ = ["BigtableStorage"]
