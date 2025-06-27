"""High level token distribution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class SplTokenArgs:
    token_account_address: str
    mint: str
    decimals: int = 0


class TokenClient:
    """Very small approximation of the Rust ``tokens`` CLI."""

    def __init__(self, rpc_url: str) -> None:
        self.rpc_url = rpc_url

    def build_transfer_instructions(self, destination: str, amount: int, args: SplTokenArgs) -> list:
        """Return an instruction-like structure describing a transfer."""

        return [
            {
                "program": "spl-token",
                "account": destination,
                "amount": amount,
                "mint": args.mint,
                "decimals": args.decimals,
            }
        ]


__all__ = ["TokenClient", "SplTokenArgs"]

