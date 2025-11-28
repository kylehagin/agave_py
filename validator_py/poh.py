"""Simplified Proof of History recorder and block production helpers.

This module keeps a rolling PoH chain by hashing previous outputs and emits
"tick" hashes after a configured number of hashes. A lightweight block
producer consumes ticks to assign slots and hand completed blocks back to the
validator for registration and gossip.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .transaction import Transaction


@dataclass
class PoHEntry:
    hash: bytes
    num_hashes: int
    mixins: List[bytes] = field(default_factory=list)


@dataclass
class PoHRecorder:
    """Minimal PoH recorder that emits a tick after a fixed hash interval."""

    hashes_per_tick: int = 32
    last_hash: bytes = field(default_factory=lambda: bytes(32))
    hash_count: int = 0
    entries: List[PoHEntry] = field(default_factory=list)

    def record(self, data: bytes = b"") -> Optional[bytes]:
        """Record a PoH hash; return the tick hash when a tick boundary is hit."""
        self.last_hash = hashlib.sha256(self.last_hash + data).digest()
        self.hash_count += 1
        if self.hash_count % self.hashes_per_tick == 0:
            entry = PoHEntry(self.last_hash, self.hash_count, [])
            self.entries.append(entry)
            return self.last_hash
        return None

    def mixin(self, payload: bytes) -> None:
        """Mix transaction data into the current PoH state."""
        self.last_hash = hashlib.sha256(self.last_hash + payload).digest()
        if self.entries:
            self.entries[-1].mixins.append(payload)

    def reset(self, seed: bytes | None = None) -> None:
        self.last_hash = seed if seed is not None else bytes(32)
        self.hash_count = 0
        self.entries.clear()

    def mixin_many(self, payloads: List[bytes]) -> None:
        for payload in payloads:
            self.mixin(payload)

    def to_snapshot(self) -> dict:
        return {
            "last_hash": self.last_hash.hex(),
            "hash_count": self.hash_count,
            "hashes_per_tick": self.hashes_per_tick,
            "entries": [
                {"hash": e.hash.hex(), "num_hashes": e.num_hashes, "mixins": [m.hex() for m in e.mixins]} for e in self.entries
            ],
        }

    @classmethod
    def from_snapshot(cls, data: dict) -> "PoHRecorder":
        recorder = cls(hashes_per_tick=data.get("hashes_per_tick", 32))
        last_hash_hex = data.get("last_hash")
        recorder.last_hash = bytes.fromhex(last_hash_hex) if last_hash_hex else bytes(32)
        recorder.hash_count = data.get("hash_count", 0)
        recorder.entries = []
        for entry in data.get("entries", []):
            recorder.entries.append(
                PoHEntry(
                    hash=bytes.fromhex(entry.get("hash", "")),
                    num_hashes=entry.get("num_hashes", 0),
                    mixins=[bytes.fromhex(m) for m in entry.get("mixins", [])],
                )
            )
        return recorder


class LeaderSchedule:
    """Deterministic leader schedule derived from stake weights."""

    def __init__(self, stakes: Dict[str, float], slots_per_epoch: int = 64):
        self.stakes = stakes
        self.slots_per_epoch = slots_per_epoch
        self._ordered = self._build_schedule()

    def _build_schedule(self) -> List[str]:
        ordered: List[str] = []
        validators = list(self.stakes.items())
        validators.sort(key=lambda kv: kv[1], reverse=True)
        for _ in range(self.slots_per_epoch):
            for identity, _ in validators:
                ordered.append(identity)
        return ordered

    def leader_for_slot(self, slot: int) -> Optional[str]:
        if not self._ordered:
            return None
        return self._ordered[slot % len(self._ordered)]


class BlockProducer:
    """Simple block producer that ties PoH ticks to slot progression."""

    def __init__(
        self,
        register_block: Callable[[bytes, int, Optional[str], List[Transaction]], asyncio.Future | asyncio.Task | None],
        poh: PoHRecorder,
        ticks_per_slot: int = 8,
        hash_interval: float = 0.05,
        leader_schedule: Optional[List[str]] = None,
        identity: Optional[str] = None,
        slot_offset: int = 0,
    ):
        self._register_block = register_block
        self._poh = poh
        self._ticks_per_slot = ticks_per_slot
        self._hash_interval = hash_interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._slot_tick = 0
        self._pending: List[Transaction] = []
        self._leader_schedule = leader_schedule or ([] if identity is None else [identity])
        self._identity = identity
        self._current_leader_index = 0
        self._last_blockhash: Optional[bytes] = None
        self._slot_offset = slot_offset

    def record_transaction(self, tx: Transaction) -> None:
        self._pending.append(tx)
        if tx.signature:
            self._poh.mixin(tx.signature)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            await self._task
            self._task = None

    async def _run(self) -> None:
        while self._running:
            tick = self._poh.record()
            if tick is not None:
                self._slot_tick += 1
                if self._slot_tick >= self._ticks_per_slot:
                    await self._emit_block(tick)
                    self._slot_tick = 0
            await asyncio.sleep(self._hash_interval)

    async def _emit_block(self, tick_hash: bytes) -> None:
        block_txs = list(self._pending)
        self._pending.clear()
        leader = None
        if self._leader_schedule:
            leader = self._leader_schedule[(self._current_leader_index + self._slot_offset) % len(self._leader_schedule)]
            self._current_leader_index += 1
            if self._identity is not None and leader != self._identity:
                # Skip block production if we're not the scheduled leader.
                return
        parent_hash = self._last_blockhash.hex() if self._last_blockhash else None
        result = self._register_block(tick_hash, self._poh.hash_count, parent_hash, block_txs)
        self._last_blockhash = tick_hash
        # Allow synchronous register_block hooks.
        if asyncio.iscoroutine(result):
            await result


class PoHVerifier:
    """Lightweight verifier for PoH entries.

    This checks hash chaining, tick spacing, and optional mixins to ensure the
    produced blocks are self-consistent for downstream replay.
    """

    def __init__(self, hashes_per_tick: int = 32):
        self.hashes_per_tick = hashes_per_tick

    def verify_entries(self, entries: List[PoHEntry]) -> bool:
        if not entries:
            return True
        prev_hash = bytes(32)
        expected_count = 0
        for entry in entries:
            if entry.num_hashes % self.hashes_per_tick != 0:
                return False
            current = prev_hash
            for _ in range(self.hashes_per_tick):
                current = hashlib.sha256(current).digest()
            if entry.mixins:
                for mix in entry.mixins:
                    current = hashlib.sha256(current + mix).digest()
            if current != entry.hash:
                return False
            prev_hash = entry.hash
            expected_count = max(expected_count, entry.num_hashes)
        return True

