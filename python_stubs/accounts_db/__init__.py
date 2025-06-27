"""Python stub for the ``accounts-db`` crate.

Only a handful of helper types that are re-exported by the Rust crate are
represented here.  They are primarily used when interacting with Solana's
account hash cache tooling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CacheHashDataFileEntry:
    """Entry within a cache hash data file."""

    hash: int
    lamports: int
    pubkey: str


@dataclass
class ParsedCacheHashDataFilename:
    """Result returned by :func:`parse_cache_hash_data_filename`."""

    slot_range_start: int
    slot_range_end: int
    bin_range_start: int
    bin_range_end: int
    hash: int


@dataclass
class CacheHashDataFileHeader:
    """Header information stored at the start of a cache hash data file."""

    count: int


def parse_cache_hash_data_filename(path: str) -> Optional[ParsedCacheHashDataFilename]:
    """Parse ``path`` into a :class:`ParsedCacheHashDataFilename` if possible."""

    parts = path.split(".")
    if len(parts) != 5:
        return None
    try:
        slot_range_start = int(parts[0])
        slot_range_end = int(parts[1])
        bin_range_start = int(parts[2])
        bin_range_end = int(parts[3])
        hash_value = int(parts[4], 16)
    except ValueError:
        return None
    return ParsedCacheHashDataFilename(
        slot_range_start,
        slot_range_end,
        bin_range_start,
        bin_range_end,
        hash_value,
    )

