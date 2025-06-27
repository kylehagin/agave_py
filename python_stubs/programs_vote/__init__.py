"""Python translation of the `programs/vote` crate."""

from typing import Deque, Iterable, Optional, Any

DEFAULT_COMPUTE_UNITS: int = 2_100


def from_account(account: Any) -> Optional["VoteState"]:
    """Deserialize a vote state from an account.

    This stub returns ``None``.
    """
    return None


def to_account(versioned: Any, account: Any) -> Optional[None]:
    """Serialize a vote state into an account.

    This is a no-op placeholder and always returns ``None``.
    """
    return None


def process_new_vote_state(vote_state: Any, new_state: Deque[Any], new_root: Optional[int], timestamp: Optional[int], epoch: int, current_slot: int) -> None:
    """Placeholder for the `process_new_vote_state` logic."""
    pass


def process_vote_unfiltered(vote_state: Any, vote: Any) -> None:
    """Placeholder for `process_vote_unfiltered`."""
    pass


def process_vote(vote_state: Any, vote: Any) -> None:
    """Placeholder for `process_vote`."""
    pass


def authorize(vote_state: Any, new_authority: str, authorization_type: Any, signers: Iterable[str]) -> None:
    """Placeholder for vote authorization logic."""
    pass
