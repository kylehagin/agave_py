"""Minimal runtime environment used by other stubs.

The real `runtime` crate in Rust is responsible for executing transactions and
maintaining account state.  Here we implement a tiny subset of that behaviour
using pure Python.  The goal is to provide something that higher level stubs
can interact with when running unit tests.

This implementation keeps state in memory and performs no signature or program
verification.  It merely tracks account balances and transaction history.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Account:
    """In-memory representation of an account."""

    owner: str
    balance: int = 0


@dataclass
class RuntimeTransaction:
    """Simple transaction structure used by :class:`Runtime`."""

    sender: str
    receiver: str
    amount: int


class Runtime:
    """Very small transaction processor."""

    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}
        self._history: List[RuntimeTransaction] = []

    def get_balance(self, owner: str) -> int:
        return self._accounts.get(owner, Account(owner)).balance

    def create_account(self, owner: str, balance: int = 0) -> None:
        if owner not in self._accounts:
            self._accounts[owner] = Account(owner, balance)

    def process_transaction(self, tx: RuntimeTransaction) -> bool:
        sender = self._accounts.get(tx.sender)
        receiver = self._accounts.get(tx.receiver)
        if sender is None or sender.balance < tx.amount:
            return False
        if receiver is None:
            receiver = Account(tx.receiver, 0)
            self._accounts[tx.receiver] = receiver
        sender.balance -= tx.amount
        receiver.balance += tx.amount
        self._history.append(tx)
        return True


__all__ = ["Runtime", "RuntimeTransaction", "Account"]
