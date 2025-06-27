"""Stub for the ``bench-vote`` binary."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    """Execute the vote benchmark (stub)."""

    parser = argparse.ArgumentParser(prog="bench-vote")
    parser.add_argument("--num_producers", type=int, default=1)
    parser.parse_args(argv)
    print("bench-vote stub executed")

