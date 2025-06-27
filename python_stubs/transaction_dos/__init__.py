"""Minimal load generator used for stress testing."""

from __future__ import annotations

import asyncio
import argparse


async def generate_load(rpc_url: str, iterations: int) -> None:
    """Simulate sending many transactions."""

    for _ in range(iterations):
        await asyncio.sleep(0)  # network placeholder


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="transaction-dos tool")
    parser.add_argument("--rpc-url", required=True)
    parser.add_argument("--iterations", type=int, default=1)
    args = parser.parse_args(argv)

    asyncio.run(generate_load(args.rpc_url, args.iterations))


__all__ = ["generate_load", "main"]

