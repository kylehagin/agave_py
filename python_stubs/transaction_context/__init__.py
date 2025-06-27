"""Simplified transaction context data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


IndexOfAccount = int


@dataclass
class InstructionAccount:
    index_in_transaction: IndexOfAccount
    is_signer: bool = False
    is_writable: bool = False


@dataclass
class TransactionAccounts:
    accounts: Dict[IndexOfAccount, Dict] = field(default_factory=dict)

    def add(self, index: IndexOfAccount, account: Dict) -> None:
        self.accounts[index] = account

    def get(self, index: IndexOfAccount) -> Optional[Dict]:
        return self.accounts.get(index)


__all__ = ["InstructionAccount", "TransactionAccounts", "IndexOfAccount"]

