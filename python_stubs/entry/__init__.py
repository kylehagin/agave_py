"""Simplified Proof of History entry utilities."""

from dataclasses import dataclass, field
from hashlib import sha256
from typing import List, Iterable


def _hash(data: bytes) -> bytes:
    return sha256(data).digest()


@dataclass
class Poh:
    """Minimal POH implementation used for tests."""

    hash: bytes
    hashes_per_tick: int = 1
    num_hashes: int = 0

    def hash_many(self, count: int) -> None:
        for _ in range(count):
            self.hash = _hash(self.hash)
            self.num_hashes += 1

    def tick(self) -> bytes:
        self.hash = _hash(self.hash)
        self.num_hashes += 1
        return self.hash


@dataclass
class Entry:
    num_hashes: int
    hash: bytes
    transactions: List[bytes] = field(default_factory=list)

    def is_tick(self) -> bool:
        return not self.transactions

    def verify(self, start_hash: bytes) -> bool:
        poh = Poh(start_hash)
        poh.hash_many(self.num_hashes - 1)
        if self.transactions:
            tx_hash = sha256(b"".join(self.transactions)).digest()
            poh.hash = _hash(poh.hash + tx_hash)
        else:
            poh.tick()
        return poh.hash == self.hash


def next_hash(start_hash: bytes, num_hashes: int, txs: Iterable[bytes]) -> bytes:
    poh = Poh(start_hash)
    poh.hash_many(max(num_hashes - 1, 0))
    if txs:
        tx_hash = sha256(b"".join(txs)).digest()
        return _hash(poh.hash + tx_hash)
    if num_hashes:
        return _hash(poh.hash)
    return start_hash

