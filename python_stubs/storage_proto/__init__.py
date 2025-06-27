"""Light-weight protocol messages used by :mod:`storage_bigtable`.

Only a couple of message types are represented here.  They mirror the data that
would be stored in Solana's Bigtable instance but omit all protobuf machinery.
"""

from dataclasses import dataclass


@dataclass
class BlockInfo:
    slot: int
    block_hash: str


__all__ = ["BlockInfo"]
