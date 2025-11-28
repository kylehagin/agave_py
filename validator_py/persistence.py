"""Persistence and bootstrap helpers for the validator prototype.

This module provides disk-backed snapshots for the ledger, consensus fork
tracking, and PoH recorder so a validator can restart without losing state.
Snapshots are written periodically and include a checksum for basic integrity
validation. Blocks are also persisted individually to allow incremental replay
between snapshots.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Optional, Tuple

from .consensus import Consensus
from .crypto import Keypair, sign, verify
from .ledger import Ledger
from .poh import PoHRecorder
from .transaction import Transaction


def _atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
    tmp.replace(path)


class SnapshotManager:
    """Coordinate ledger snapshots and block persistence for restart safety."""

    def __init__(
        self,
        base_dir: str = "validator_ledger",
        full_snapshot_interval: int = 200,
        incremental_snapshot_interval: int = 25,
        signing_keypair: Keypair | None = None,
        expected_authority: str | None = None,
    ) -> None:
        self.base = Path(base_dir)
        self.snapshots = self.base / "snapshots"
        self.blocks = self.base / "blocks"
        self.full_interval = max(1, full_snapshot_interval)
        self.incremental_interval = max(1, incremental_snapshot_interval)
        self.snapshots.mkdir(parents=True, exist_ok=True)
        self.blocks.mkdir(parents=True, exist_ok=True)
        self.signing_keypair = signing_keypair
        self.expected_authority = expected_authority

    def _checksum(self, state: dict) -> str:
        payload = json.dumps(state, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()

    def _snapshot_payload(self, slot: int, ledger: Ledger, consensus: Consensus, poh: PoHRecorder) -> dict:
        state = {
            "ledger": ledger.to_snapshot(),
            "consensus": consensus.to_snapshot(),
            "poh": poh.to_snapshot(),
        }
        payload = {"slot": slot, "state": state, "checksum": self._checksum(state), "version": 1}
        if self.signing_keypair:
            payload["authority"] = self.signing_keypair.public_key.hex()
            payload["signature"] = sign(payload["checksum"].encode(), self.signing_keypair).hex()
        return payload

    def _write_snapshot(self, path: Path, payload: dict) -> None:
        _atomic_write(path, payload)

    def persist_block(
        self,
        slot: int,
        blockhash: str,
        parent: Optional[str],
        hash_height: Optional[int],
        transactions: Iterable[Transaction],
    ) -> None:
        record = {
            "slot": slot,
            "blockhash": blockhash,
            "parent": parent,
            "hash_height": hash_height,
            "transactions": [tx.to_bytes().hex() for tx in transactions],
        }
        record["checksum"] = self._checksum(record)
        path = self.blocks / f"{slot:020d}.json"
        _atomic_write(path, record)

    def maybe_snapshot(self, slot: int, ledger: Ledger, consensus: Consensus, poh: PoHRecorder) -> None:
        if slot == 0:
            return
        if slot % self.full_interval == 0:
            payload = self._snapshot_payload(slot, ledger, consensus, poh)
            self._write_snapshot(self.snapshots / f"full-{slot:020d}.json", payload)
        elif slot % self.incremental_interval == 0:
            payload = self._snapshot_payload(slot, ledger, consensus, poh)
            payload["base_slot"] = self._latest_full_slot()
            self._write_snapshot(self.snapshots / f"incremental-{slot:020d}.json", payload)

    def _latest_full_slot(self) -> Optional[int]:
        slots = []
        for path in self.snapshots.glob("full-*.json"):
            try:
                slots.append(int(path.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return max(slots) if slots else None

    def _load_snapshot(self, path: Path) -> tuple[int, Ledger, Consensus, PoHRecorder]:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        slot = int(payload.get("slot", 0))
        state = payload.get("state", {})
        checksum = payload.get("checksum")
        if checksum is not None and checksum != self._checksum(state):
            raise ValueError(f"Snapshot checksum mismatch for {path}")
        if self.expected_authority is not None:
            authority = payload.get("authority")
            signature = payload.get("signature")
            if authority != self.expected_authority:
                raise ValueError("Snapshot authority mismatch")
            if signature is None:
                raise ValueError("Snapshot missing signature")
            if not verify(checksum.encode(), bytes.fromhex(signature), bytes.fromhex(authority)):
                raise ValueError("Snapshot signature invalid")
        ledger = Ledger.from_snapshot(state.get("ledger", {}))
        consensus = Consensus.from_snapshot(state.get("consensus", {}))
        poh = PoHRecorder.from_snapshot(state.get("poh", {}))
        return slot, ledger, consensus, poh

    def _sorted_snapshots(self) -> list[Path]:
        paths = []
        for path in self.snapshots.glob("*.json"):
            try:
                slot = int(path.stem.split("-", 1)[1])
            except (IndexError, ValueError):
                continue
            paths.append((slot, path))
        return [p for _, p in sorted(paths, key=lambda x: x[0])]

    def bootstrap(self) -> Optional[Tuple[int, Ledger, Consensus, PoHRecorder]]:
        snapshots = list(reversed(self._sorted_snapshots()))
        if not snapshots:
            return None
        slot = 0
        ledger = None
        consensus = None
        poh = None
        for candidate in snapshots:
            try:
                slot, ledger, consensus, poh = self._load_snapshot(candidate)
                break
            except Exception:
                continue
        if ledger is None or consensus is None or poh is None:
            return None
        # Replay any persisted blocks beyond the snapshot slot.
        for block_path in sorted(self.blocks.glob("*.json")):
            try:
                block_slot = int(block_path.stem)
            except ValueError:
                continue
            if block_slot <= slot:
                continue
            try:
                with block_path.open("r", encoding="utf-8") as fh:
                    block = json.load(fh)
                blockhash = block.get("blockhash")
                parent = block.get("parent")
                hash_height = block.get("hash_height")
                txs = []
                for raw in block.get("transactions", []):
                    try:
                        tx_bytes = bytes.fromhex(raw)
                        txs.append(Transaction.from_bytes(tx_bytes))
                    except Exception:
                        continue
                expected_checksum = block.get("checksum")
                if expected_checksum and expected_checksum != self._checksum({k: v for k, v in block.items() if k != "checksum"}):
                    continue
                ledger.record_block(block_slot, blockhash, parent, hash_height, txs)
                for tx in txs:
                    ledger.process_transaction(tx)
                consensus.register_block(block_slot, blockhash, parent)
                if hash_height is not None:
                    poh.hash_count = max(poh.hash_count, hash_height)
                if isinstance(blockhash, str):
                    try:
                        poh.last_hash = bytes.fromhex(blockhash)
                    except ValueError:
                        pass
                slot = max(slot, block_slot)
            except Exception:
                continue
        return slot, ledger, consensus, poh

