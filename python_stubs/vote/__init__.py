"""Voting utilities for simple consensus simulations."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class VoteAccount:
    pubkey: str
    stake: int = 0
    votes: List[int] = field(default_factory=list)

    def submit_vote(self, slot: int) -> None:
        self.votes.append(slot)


class VoteRegistry:
    """Track votes from multiple accounts."""

    def __init__(self):
        self.accounts: Dict[str, VoteAccount] = {}

    def register(self, pubkey: str, stake: int = 0) -> VoteAccount:
        acct = VoteAccount(pubkey, stake)
        self.accounts[pubkey] = acct
        return acct

    def record_vote(self, pubkey: str, slot: int) -> None:
        acct = self.accounts.get(pubkey)
        if acct:
            acct.submit_vote(slot)


__all__ = ["VoteAccount", "VoteRegistry"]

