"""Simplified model of the Solana faucet service."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FaucetRequest:
    lamports: int
    to: str
    blockhash: str


@dataclass
class FaucetTransaction:
    tx: object
    memo: Optional[str] = None


class Faucet:
    """Very small approximation of the Rust ``Faucet`` struct."""

    def __init__(self, faucet_keypair: str):
        self.faucet_keypair = faucet_keypair
        self.ip_cache: Dict[str, int] = {}

    def build_airdrop_transaction(self, req: FaucetRequest, ip: str) -> FaucetTransaction:
        """Build a fake airdrop transaction."""

        # TODO: enforce per-request and per-time limits
        tx = {
            "from": self.faucet_keypair,
            "to": req.to,
            "lamports": req.lamports,
            "blockhash": req.blockhash,
        }
        return FaucetTransaction(tx)

