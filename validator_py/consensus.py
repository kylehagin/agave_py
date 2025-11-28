from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class VoteRecord:
    voter: str
    slot: int
    stake: int = 1


@dataclass
class LockoutVote:
    slot: int
    confirmation_count: int


@dataclass
class BlockEntry:
    slot: int
    blockhash: str
    parent: Optional[str]
    children: Set[str] = field(default_factory=set)
    votes: Dict[str, VoteRecord] = field(default_factory=dict)

    @property
    def weight(self) -> int:
        return sum(v.stake for v in self.votes.values())


class Consensus:
    """Minimal fork-choice and vote tracking for the validator prototype."""

    def __init__(self, identity: str, stake: int = 1, vote_lockout: int = 2):
        self.identity = identity
        self.stake = stake
        self.blocks: Dict[str, BlockEntry] = {}
        self.root: Optional[str] = None
        self.best: Optional[str] = None
        # Tower BFT-inspired vote lockouts; confirmation count doubles each vote depth.
        self.vote_lockout = vote_lockout
        self.lockout_history: List[LockoutVote] = []
        self.slashed: Set[str] = set()
        self.replay_log: List[Tuple[int, str]] = []

    def ensure_block(self, blockhash: str, slot: int, parent: Optional[str] = None) -> BlockEntry:
        if blockhash not in self.blocks:
            self.blocks[blockhash] = BlockEntry(slot=slot, blockhash=blockhash, parent=parent)
        entry = self.blocks[blockhash]
        # If we learn about a parent later, fill it in so fork traversal works.
        if entry.parent is None and parent is not None:
            entry.parent = parent
        return entry

    def register_block(self, slot: int, blockhash: str, parent: Optional[str]) -> None:
        entry = self.ensure_block(blockhash, slot, parent)
        if parent is not None:
            parent_entry = self.ensure_block(parent, slot - 1, None)
            parent_entry.children.add(blockhash)
        if self.root is None:
            self.root = blockhash
        self._update_best()

    def record_vote(self, voter: str, blockhash: str, stake: int | None = None, slot: Optional[int] = None) -> None:
        entry = self.blocks.get(blockhash)
        if entry is None:
            # Unknown block; create a placeholder so the vote is not lost.
            assumed_slot = slot if slot is not None else 0
            entry = self.ensure_block(blockhash, assumed_slot, None)
        weight = stake if stake is not None else 1
        if slot is None:
            slot = entry.slot
        self._detect_slashable_vote(voter, slot, blockhash)
        entry.votes[voter] = VoteRecord(voter=voter, slot=slot, stake=weight)
        if voter == self.identity:
            self._record_lockout_vote(slot)
        self._update_best()

    def _detect_slashable_vote(self, voter: str, slot: int, blockhash: str) -> None:
        """Mark validators that cast conflicting votes for the same slot."""

        for bh, entry in self.blocks.items():
            if bh == blockhash:
                continue
            if voter in entry.votes and entry.votes[voter].slot == slot:
                self.slashed.add(voter)
                break

    def _cumulative_weight(self, blockhash: str) -> int:
        weight = 0
        cursor = self.blocks.get(blockhash)
        visited = set()
        while cursor is not None and cursor.blockhash not in visited:
            visited.add(cursor.blockhash)
            weight += cursor.weight
            if cursor.parent is None:
                break
            cursor = self.blocks.get(cursor.parent)
        return weight

    def _record_lockout_vote(self, slot: int) -> None:
        """Update lockout history, pruning expired votes and advancing the root.

        This is a lightweight nod to Tower BFT: confirmation counts double with
        depth, earlier votes may be popped if they conflict with the new slot,
        and the oldest surviving vote establishes the rooted slot once its
        lockout is satisfied.
        """

        self.lockout_history.append(LockoutVote(slot=slot, confirmation_count=1))
        # Bubble confirmations forward.
        for idx in range(len(self.lockout_history) - 1, -1, -1):
            vote = self.lockout_history[idx]
            duration = self.vote_lockout * (2 ** (len(self.lockout_history) - idx - 1))
            if slot - vote.slot < duration:
                continue
            vote.confirmation_count += 1
        # Remove expired votes that no longer influence safety.
        self.lockout_history = [v for v in self.lockout_history if slot - v.slot < self.vote_lockout * (2 ** v.confirmation_count)]
        if self.lockout_history:
            rooted = self.lockout_history[0]
            # Find the highest blockhash at or before rooted.slot and root the fork.
            rooted_hash = None
            for bh, entry in self.blocks.items():
                if entry.slot == rooted.slot:
                    rooted_hash = bh
                    break
            if rooted_hash:
                self.root = rooted_hash

    def _update_best(self) -> None:
        if not self.blocks:
            return
        tips = [bh for bh, entry in self.blocks.items() if not entry.children]
        if not tips:
            tips = list(self.blocks.keys())
        best_hash = None
        best_weight = -1
        best_slot = -1
        for tip in tips:
            weight = self._cumulative_weight(tip)
            slot = self.blocks[tip].slot
            if weight > best_weight or (weight == best_weight and slot > best_slot):
                best_hash = tip
                best_weight = weight
                best_slot = slot
        self.best = best_hash

    def best_blockhash(self) -> Optional[str]:
        return self.best

    def vote_message(self, voter: str, slot: int, blockhash: str) -> bytes:
        return f"VOTE {voter} {slot} {blockhash}".encode()

    def to_snapshot(self) -> dict:
        blocks = {}
        for bh, entry in self.blocks.items():
            blocks[bh] = {
                "slot": entry.slot,
                "parent": entry.parent,
                "children": list(entry.children),
                "votes": {voter: {"slot": v.slot, "stake": v.stake} for voter, v in entry.votes.items()},
            }
        return {
            "identity": self.identity,
            "stake": self.stake,
            "blocks": blocks,
            "root": self.root,
            "best": self.best,
            "vote_lockout": self.vote_lockout,
            "lockout_history": [vars(v) for v in self.lockout_history],
            "slashed": list(self.slashed),
            "replay_log": self.replay_log,
        }

    @classmethod
    def from_snapshot(cls, data: dict) -> "Consensus":
        consensus = cls(
            identity=data.get("identity", ""),
            stake=data.get("stake", 1),
            vote_lockout=data.get("vote_lockout", 2),
        )
        consensus.root = data.get("root")
        consensus.best = data.get("best")
        consensus.lockout_history = [LockoutVote(**vote) for vote in data.get("lockout_history", [])]
        consensus.slashed = set(data.get("slashed", []))
        consensus.replay_log = [tuple(item) for item in data.get("replay_log", [])]
        for bh, entry in data.get("blocks", {}).items():
            block_entry = consensus.ensure_block(bh, entry.get("slot", 0), entry.get("parent"))
            block_entry.children = set(entry.get("children", []))
            votes = entry.get("votes", {})
            for voter, vote in votes.items():
                block_entry.votes[voter] = VoteRecord(voter=voter, slot=vote.get("slot", 0), stake=vote.get("stake", 1))
        consensus._update_best()
        return consensus

    def record_replay(self, slot: int, blockhash: str) -> None:
        """Track replayed slots to integrate with a replay-stage like pipeline."""

        self.replay_log.append((slot, blockhash))
        # If replay reaches the best tip, advance root for safety.
        if self.best == blockhash:
            self.root = blockhash

    def is_slashed(self, identity: str) -> bool:
        return identity in self.slashed
