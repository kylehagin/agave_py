"""In-memory implementation of the ``accounts-bench`` utility.

The real Rust executable benchmarks various ``AccountsDb`` operations.  The
Python version provides a small approximation of that behaviour so tests can
exercise similar logic without requiring a validator.  It keeps all state in
memory and uses the ``hashlib`` and ``time`` modules to measure work."""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import shutil
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Account:
    """Very small representation of an account."""

    lamports: int


class AccountsBench:
    """Collection of accounts used for benchmarking."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.accounts: dict[str, Account] = {}

    def create_accounts(self, pubkeys: list[str], count: int, slot: int) -> None:
        for i in range(count):
            pubkey = f"{slot}-{i}-{random.getrandbits(64):016x}"
            self.accounts[pubkey] = Account(i + 1)
            pubkeys.append(pubkey)

    def update_accounts(self, pubkeys: list[str], slot: int) -> None:
        for pubkey in pubkeys:
            self.accounts[pubkey].lamports = random.randint(0, 9)

    def clean_accounts(self) -> None:
        self.accounts = {k: v for k, v in self.accounts.items() if v.lamports}

    def calculate_hash(self) -> str:
        hasher = hashlib.sha256()
        for pubkey in sorted(self.accounts.keys()):
            hasher.update(pubkey.encode("utf-8"))
            hasher.update(self.accounts[pubkey].lamports.to_bytes(8, "little"))
        return hasher.hexdigest()


def main(argv: list[str] | None = None) -> None:
    """Run the accounts benchmark."""

    parser = argparse.ArgumentParser(prog="accounts-bench")
    parser.add_argument("--num_slots", type=int, default=4)
    parser.add_argument("--num_accounts", type=int, default=10_000)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args(argv)

    path = Path(os.environ.get("FARF_DIR", "farf")) / "accounts-bench"
    print(f"cleaning file system: {path}")
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)

    bench = AccountsBench(path)
    pubkeys: list[str] = []

    for slot in range(args.num_slots):
        bench.create_accounts(pubkeys, args.num_accounts // args.num_slots, slot)

    elapsed: list[int] = []
    elapsed_store: list[int] = []

    for iteration in range(args.iterations):
        if args.clean:
            start = time.perf_counter()
            bench.clean_accounts()
            clean_us = int((time.perf_counter() - start) * 1_000_000)
            print(f"clean {clean_us}us")
            for slot in range(args.num_slots):
                bench.update_accounts(pubkeys, (iteration + 1) * args.num_slots + slot)
        else:
            start = time.perf_counter()
            hash1 = bench.calculate_hash()
            time_hash = (time.perf_counter() - start) * 1_000_000

            start_store = time.perf_counter()
            hash2 = bench.calculate_hash()
            time_store = (time.perf_counter() - start_store) * 1_000_000

            if hash1 != hash2:
                print("hash mismatch")

            ratio = 0 if time_hash == 0 else int(time_store / time_hash * 100)
            print(f"hash,{hash1},{int(time_hash)}us,{int(time_store)}us,{ratio}%")

            bench.create_accounts(pubkeys, 1, 0)
            elapsed.append(int(time_hash))
            elapsed_store.append(int(time_store))

    for value in elapsed:
        print(f"update_accounts_hash(us),{value}")
    for value in elapsed_store:
        print(f"calculate_accounts_hash_from_storages(us),{value}")

