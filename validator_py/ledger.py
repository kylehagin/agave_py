import json
import os
from collections import deque
from typing import Dict, Optional

from .crypto import verify
from .runtime import Account, Bank
from .transaction import Transaction, WireTransactionParseError, parse_wire_transaction

class Ledger:
    def __init__(self):
        self.bank = Bank()
        self.history = []
        self.recent_blockhashes: deque[str] = deque(maxlen=150)
        self.blockhash_expirations: Dict[str, int] = {}
        self.block_slots: Dict[str, int] = {}
        self.block_parents: Dict[str, str | None] = {}
        self.slot_hashes: Dict[int, str] = {}
        self.hash_heights: Dict[str, int] = {}
        self.block_transactions: Dict[int, list[str]] = {}
        self.blocks: Dict[int, dict] = {}
        self.tx_status: Dict[str, dict] = {}
        self.tx_store: Dict[str, Transaction] = {}
        self._persistent_dir: Optional[str] = None
        # Seed with a genesis blockhash so transactions have a starting point.
        self.recent_blockhashes.append("0" * 64)
        self.block_slots["0" * 64] = 0
        self.blockhash_expirations["0" * 64] = 0
        self.block_parents["0" * 64] = None
        self.slot_hashes[0] = "0" * 64
        self.hash_heights["0" * 64] = 0

    def create_account(self, owner: str, balance: int = 0) -> None:
        """Create a new account with the given balance."""
        self.bank.ensure_account(owner, balance)

    def get_balance(self, owner: str) -> int:
        """Return the current balance for an owner."""
        return self.bank.get_balance(owner)

    def process_transaction(self, tx: Transaction) -> bool:
        if tx.wire_bytes is not None and (tx.sender is None or tx.signature is None):
            try:
                parsed = parse_wire_transaction(tx.wire_bytes)
            except WireTransactionParseError:
                return False

            if not self._blockhash_is_recent(parsed.recent_blockhash):
                return False

            if parsed.num_required_signatures > len(parsed.signatures):
                return False

            for signer_index in range(parsed.num_required_signatures):
                signature = parsed.signatures[signer_index]
                try:
                    signer_pk = parsed.account_keys[signer_index]
                except IndexError:
                    return False
                if not verify(parsed.message, signature, signer_pk):
                    return False

            if parsed.signatures:
                tx.signature = parsed.signatures[0]
                sig_hex = parsed.signatures[0].hex()
                self.tx_store[sig_hex] = tx
                self.tx_status.setdefault(sig_hex, {"slot": None, "err": None, "blockhash": parsed.recent_blockhash})

            if not self.bank.process_legacy_transaction(parsed):
                return False

            self.history.append(tx)
            self._persist_transaction(sig_hex, slot=None)
            return True

        if (
            tx.sender is None
            or tx.receiver is None
            or tx.amount is None
            or tx.signature is None
            or tx.recent_blockhash is None
        ):
            return False

        if not self._blockhash_is_recent(tx.recent_blockhash):
            return False

        payload = f"{tx.sender}->{tx.receiver}:{tx.amount}:{tx.recent_blockhash}".encode()
        try:
            sender_pk = bytes.fromhex(tx.sender)
        except ValueError:
            return False

        if not verify(payload, tx.signature, sender_pk):
            return False
        if not self.bank.process_transfer(tx.sender, tx.receiver, tx.amount, num_signatures=1):
            return False
        self.history.append(tx)
        sig_hex = tx.signature.hex()
        self.tx_store[sig_hex] = tx
        self.tx_status.setdefault(sig_hex, {"slot": None, "err": None, "blockhash": tx.recent_blockhash})
        self._persist_transaction(sig_hex, slot=None)
        return True

    def register_blockhash(
        self, blockhash: str, slot: int | None = None, parent: str | None = None, hash_height: int | None = None
    ) -> None:
        self.recent_blockhashes.append(blockhash)
        if slot is not None:
            self.block_slots[blockhash] = slot
            self.slot_hashes[slot] = blockhash
            # Blockhashes expire after 150 slots to mirror the blockhash queue horizon.
            self.blockhash_expirations[blockhash] = slot + self.recent_blockhashes.maxlen
        if parent is not None:
            self.block_parents[blockhash] = parent
        if hash_height is not None:
            self.hash_heights[blockhash] = hash_height

    def _blockhash_is_recent(self, blockhash: str | None) -> bool:
        if blockhash is None:
            return False
        if blockhash not in self.recent_blockhashes:
            return False
        latest_slot = max(self.block_slots.values() or [0])
        expires = self.blockhash_expirations.get(blockhash, latest_slot)
        return latest_slot <= expires

    def record_block(
        self, slot: int, blockhash: str, parent: str | None, hash_height: int | None, transactions: list[Transaction]
    ) -> None:
        self.register_blockhash(blockhash, slot, parent, hash_height)
        signatures = []
        for tx in transactions:
            if tx.signature is None:
                continue
            sig_hex = tx.signature.hex()
            signatures.append(sig_hex)
            status = self.tx_status.setdefault(sig_hex, {"slot": None, "err": None, "blockhash": blockhash})
            status.update({"slot": slot, "err": None, "blockhash": blockhash})
            self.tx_store[sig_hex] = tx
        self.block_transactions[slot] = signatures
        self.blocks[slot] = {
            "slot": slot,
            "blockhash": blockhash,
            "parent": parent,
            "hash_height": hash_height,
            "signatures": signatures,
        }
        self._persist_block(slot)

    def get_block(self, slot: int) -> dict | None:
        block = self.blocks.get(slot)
        if not block:
            return None
        txs = []
        for sig in block.get("signatures", []):
            meta = self.tx_status.get(sig, {})
            txs.append({"signature": sig, "slot": meta.get("slot"), "err": meta.get("err")})
        result = dict(block)
        result["transactions"] = txs
        result["previousBlockhash"] = self.block_parents.get(block["blockhash"])
        return result

    def get_transaction_status(self, signature: str) -> dict | None:
        meta = self.tx_status.get(signature)
        if not meta:
            return None
        tx = self.tx_store.get(signature)
        return {
            "signature": signature,
            "slot": meta.get("slot"),
            "err": meta.get("err"),
            "blockhash": meta.get("blockhash"),
            "transaction": tx,
        }

    def enable_persistence(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        self._persistent_dir = directory

    def _persist_transaction(self, signature: str, slot: Optional[int]) -> None:
        if not self._persistent_dir:
            return
        tx = self.tx_store.get(signature)
        if tx is None:
            return
        path = os.path.join(self._persistent_dir, f"tx-{signature}.json")
        payload = {
            "signature": signature,
            "slot": slot,
            "err": self.tx_status.get(signature, {}).get("err"),
            "blockhash": self.tx_status.get(signature, {}).get("blockhash"),
            "wire": tx.wire_bytes.hex() if tx.wire_bytes else None,
            "json": tx.to_bytes().hex(),
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def _persist_block(self, slot: int) -> None:
        if not self._persistent_dir:
            return
        block = self.get_block(slot)
        if block is None:
            return
        path = os.path.join(self._persistent_dir, f"block-{slot}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(block, fh)

    def to_snapshot(self) -> dict:
        accounts = {}
        for pubkey, acc in self.bank.accounts.items():
            accounts[pubkey] = {
                "lamports": acc.lamports,
                "owner": acc.owner.hex(),
                "data": acc.data.hex(),
                "executable": acc.executable,
            }
        return {
            "accounts": accounts,
            "stake_accounts": dict(self.bank.stake_accounts),
            "vote_accounts": dict(self.bank.vote_accounts),
            "nonce_accounts": dict(self.bank.nonce_accounts),
            "rent_burned": self.bank.rent_burned,
            "recent_blockhashes": list(self.recent_blockhashes),
            "blockhash_expirations": dict(self.blockhash_expirations),
            "block_slots": dict(self.block_slots),
            "block_parents": dict(self.block_parents),
            "slot_hashes": dict(self.slot_hashes),
            "hash_heights": dict(self.hash_heights),
            "block_transactions": dict(self.block_transactions),
            "blocks": dict(self.blocks),
            "tx_status": dict(self.tx_status),
            "tx_store": {k: v.to_bytes().hex() for k, v in self.tx_store.items()},
            "history": [tx.to_bytes().hex() for tx in self.history],
        }

    @classmethod
    def from_snapshot(cls, data: dict) -> "Ledger":
        ledger = cls()
        ledger.bank.accounts.clear()
        accounts = data.get("accounts", {})
        for pubkey, acc in accounts.items():
            owner_hex = acc.get("owner")
            data_hex = acc.get("data")
            ledger.bank.accounts[pubkey] = Account(
                lamports=acc.get("lamports", 0),
                owner=bytes.fromhex(owner_hex) if owner_hex else b"",
                data=bytes.fromhex(data_hex) if data_hex else b"",
                executable=bool(acc.get("executable", False)),
            )
        ledger.recent_blockhashes = deque(data.get("recent_blockhashes", []), maxlen=150)
        ledger.bank.stake_accounts = dict(data.get("stake_accounts", {}))
        ledger.bank.vote_accounts = dict(data.get("vote_accounts", {}))
        ledger.bank.nonce_accounts = dict(data.get("nonce_accounts", {}))
        ledger.bank.rent_burned = int(data.get("rent_burned", 0))
        ledger.blockhash_expirations = dict(data.get("blockhash_expirations", {}))
        ledger.block_slots = dict(data.get("block_slots", {}))
        ledger.block_parents = dict(data.get("block_parents", {}))
        ledger.slot_hashes = dict(data.get("slot_hashes", {}))
        ledger.hash_heights = dict(data.get("hash_heights", {}))
        ledger.block_transactions = dict(data.get("block_transactions", {}))
        ledger.blocks = dict(data.get("blocks", {}))
        ledger.tx_status = dict(data.get("tx_status", {}))
        ledger.tx_store = {}
        for sig, raw in data.get("tx_store", {}).items():
            try:
                ledger.tx_store[sig] = Transaction.from_bytes(bytes.fromhex(raw))
            except Exception:
                continue
        ledger.history = []
        for raw in data.get("history", []):
            try:
                ledger.history.append(Transaction.from_bytes(bytes.fromhex(raw)))
            except Exception:
                continue
        if not ledger.recent_blockhashes:
            genesis = "0" * 64
            ledger.recent_blockhashes.append(genesis)
            ledger.block_slots[genesis] = 0
            ledger.blockhash_expirations[genesis] = 0
            ledger.block_parents[genesis] = None
            ledger.slot_hashes[0] = genesis
            ledger.hash_heights[genesis] = 0
        return ledger
