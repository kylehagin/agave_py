"""Minimal stand in for the ``banks-server`` crate."""

from __future__ import annotations

from typing import Any


class BanksServer:
    """Server placeholder used during testing."""

    def __init__(self, bank_forks: Any) -> None:  # pragma: no cover - stub
        self.bank_forks = bank_forks

    def start(self) -> None:
        """Start the server (no-op in the stub)."""

        print("banks-server stub started")

