"""Python implementation of ``accounts-cluster-bench``.

The real ``accounts-cluster-bench`` crate performs a variety of RPC calls
against a Solana cluster in order to benchmark validator performance.  This
module provides a lightweight Python equivalent which can be used for simple
testing and local development.  The implementation is intentionally minimal but
mirrors the basic structure of the Rust tool so that other stubs can rely on
its behaviour.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any, Optional

MAX_RPC_CALL_RETRIES = 5


def poll_slot_height(client: Any, retries: int = MAX_RPC_CALL_RETRIES) -> int:
    """Poll ``client`` until a slot height is returned or ``retries`` expire."""

    while retries > 0:
        try:
            return client.get_slot_with_commitment("confirmed")  # type: ignore
        except Exception:  # pragma: no cover - best effort stub
            retries -= 1
            time.sleep(0.1)
    raise RuntimeError("failed to get slot height")


def poll_get_latest_blockhash(client: Any, retries: int = MAX_RPC_CALL_RETRIES) -> Optional[str]:
    """Poll ``client`` for the most recent blockhash."""

    while retries > 0:
        try:
            return client.get_latest_blockhash()  # type: ignore
        except Exception:
            retries -= 1
            time.sleep(0.1)
    return None


def poll_get_fee_for_message(client: Any, message: Any, retries: int = MAX_RPC_CALL_RETRIES) -> tuple[Optional[int], Any]:
    """Poll ``client`` for the fee of ``message`` and return the blockhash used."""

    while retries > 0:
        try:
            fee = client.get_fee_for_message(message)  # type: ignore
            return fee, getattr(message, "recent_blockhash", None)
        except Exception:
            retries -= 1
            time.sleep(0.1)
    raise RuntimeError("failed to get fee for message")


def benchmark_rpc(client: Any, iterations: int = 1) -> None:
    """Run a simplified RPC benchmark against ``client``.

    Parameters
    ----------
    client : Any
        RPC client instance implementing ``get_slot_with_commitment``,
        ``get_latest_blockhash`` and ``get_fee_for_message``.
    iterations : int
        Number of benchmark iterations to perform.
    """

    logging.info("Starting RPC benchmark for %d iteration(s)", iterations)
    message = getattr(client, "benchmark_message", object())
    for i in range(iterations):
        slot = poll_slot_height(client)
        blockhash = poll_get_latest_blockhash(client)
        fee, used_blockhash = poll_get_fee_for_message(client, message)
        logging.debug(
            "iteration=%d slot=%s blockhash=%s fee=%s used_blockhash=%s",
            i,
            slot,
            blockhash,
            fee,
            used_blockhash,
        )


def main(argv: list[str] | None = None) -> None:
    """Entry point used by the ``accounts-cluster-bench`` CLI."""

    parser = argparse.ArgumentParser(prog="accounts-cluster-bench")
    parser.add_argument("--rpc-url", default="http://localhost:8899")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--verbose", action="store_true", help="enable debug output")
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=level, format="%(message)s")

    try:
        from solana.rpc.api import Client  # pragma: no cover - optional dependency

        client = Client(args.rpc_url)
        # ``Message`` type is not required for this basic benchmark.  Create a
        # lightweight placeholder so ``get_fee_for_message`` can be exercised.
        try:
            from solana.message import Message  # type: ignore
        except Exception:  # pragma: no cover - best effort
            class Message:  # type: ignore
                recent_blockhash = None

        setattr(client, "benchmark_message", Message())
        benchmark_rpc(client, args.iterations)
    except Exception as exc:  # pragma: no cover - best effort fallback
        logging.error("Benchmark failed: %s", exc)


__all__ = [
    "benchmark_rpc",
    "main",
    "poll_get_fee_for_message",
    "poll_get_latest_blockhash",
    "poll_slot_height",
]

