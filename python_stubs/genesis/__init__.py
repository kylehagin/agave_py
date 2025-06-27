"""Structures used when generating a genesis configuration."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Base64Account:
    balance: int
    owner: str
    data: str
    executable: bool


@dataclass
class StakedValidatorAccountInfo:
    balance_lamports: int
    stake_lamports: int
    identity_account: str
    vote_account: str
    stake_account: str


@dataclass
class ValidatorAccountsFile:
    validator_accounts: List[StakedValidatorAccountInfo]


class AddressGenerator:
    """Utility to derive program addresses."""

    def __init__(self, base_pubkey: str, program_id: str):
        self.base_pubkey = base_pubkey
        self.program_id = program_id
        self.nth = 0

    def nth_address(self, n: int) -> str:
        # TODO: replicate ``Pubkey::create_with_seed`` behaviour
        return f"{self.base_pubkey}-{self.program_id}-{n}"

    def next(self) -> str:
        addr = self.nth_address(self.nth)
        self.nth += 1
        return addr

