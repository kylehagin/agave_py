from typing import Dict
from .crypto import verify
from .transaction import Transaction

class Ledger:
    def __init__(self):
        self.balances: Dict[str, int] = {}
        self.history = []

    def create_account(self, owner: str, balance: int = 0) -> None:
        """Create a new account with the given balance."""
        if owner not in self.balances:
            self.balances[owner] = balance

    def get_balance(self, owner: str) -> int:
        """Return the current balance for an owner."""
        return self.balances.get(owner, 0)

    def process_transaction(self, tx: Transaction) -> bool:
        payload = f"{tx.sender}->{tx.receiver}:{tx.amount}".encode()
        keypair_like = type("KP", (), {"private_key": bytes.fromhex(tx.sender)})()
        if not verify(payload, tx.signature, keypair_like):
            return False
        self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
        self.balances[tx.receiver] = self.balances.get(tx.receiver, 0) + tx.amount
        self.history.append(tx)
        return True
