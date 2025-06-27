"""Benchmark helpers for the compute budget program.

The original crate exposes criterion based benchmarks.  ``benchmark`` can be
used to reproduce similar measurements in Python.
"""

from __future__ import annotations

import time
from typing import Callable


def benchmark(func: Callable[[], None], iterations: int = 1) -> float:
    """Measure average execution time of ``func``."""

    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    return (end - start) / max(iterations, 1)


__all__ = ["benchmark"]

