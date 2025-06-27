"""Stub for the ``bench-streamer`` benchmarking tool."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    """Execute the streaming benchmark (stub)."""

    parser = argparse.ArgumentParser(prog="bench-streamer")
    parser.add_argument("--duration", type=int, default=5)
    parser.parse_args(argv)
    print("bench-streamer stub executed")

