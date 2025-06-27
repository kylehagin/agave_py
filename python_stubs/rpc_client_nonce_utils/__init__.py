"""Helpers for durable transaction nonces."""

from dataclasses import dataclass
from typing import Any


class Error(Exception):
    pass


def get_account(rpc_client: Any, nonce_pubkey: str) -> Any:
    """Fetch a nonce account. Placeholder returns ``None``."""
    return None


def get_account_with_commitment(rpc_client: Any, nonce_pubkey: str, commitment: Any) -> Any:
    """Fetch a nonce account with commitment. Placeholder returns ``None``."""
    return None
