"""Stub for the ``bench-tps`` throughput benchmark."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    """Run the TPS benchmark (stub)."""

    parser = argparse.ArgumentParser(prog="bench-tps")
    parser.add_argument("--tx_count", type=int, default=1000)
    parser.parse_args(argv)
    print("bench-tps stub executed")

