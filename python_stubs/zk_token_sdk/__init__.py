"""Toy zero-knowledge token operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

@dataclass
class TokenAccount:
    owner: bytes
    balance: int = 0


class TokenBank:
    def __init__(self):
        self.accounts: Dict[bytes, TokenAccount] = {}

    def create_account(self, owner: bytes) -> TokenAccount:
        acct = TokenAccount(owner)
        self.accounts[owner] = acct
        return acct

    def transfer(self, sender: TokenAccount, receiver: TokenAccount, amount: int) -> None:
        if sender.balance < amount:
            raise ValueError("insufficient funds")
        sender.balance -= amount
        receiver.balance += amount


__all__ = ["TokenAccount", "TokenBank"]

