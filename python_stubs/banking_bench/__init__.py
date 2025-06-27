"""Stub for the ``banking-bench`` utility."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    """Run the banking benchmark (stubbed)."""

    parser = argparse.ArgumentParser(prog="banking-bench")
    parser.add_argument("--transactions", type=int, default=1000)
    parser.parse_args(argv)
    print("banking-bench stub executed")

