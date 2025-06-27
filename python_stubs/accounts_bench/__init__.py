"""Python stub for the ``accounts-bench`` executable.

The real program benchmarks various account database operations within a
Solana validator.  The Python version only exposes a :func:`main` function that
prints out the arguments it would have processed.
"""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    """Entry point used by the CLI stub."""

    parser = argparse.ArgumentParser(prog="accounts-bench")
    parser.add_argument("--num_slots", type=int, default=4)
    parser.add_argument("--num_accounts", type=int, default=10_000)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args(argv)

    print(
        "accounts-bench stub: slots=%d accounts=%d iterations=%d clean=%s"
        % (args.num_slots, args.num_accounts, args.iterations, args.clean)
    )

