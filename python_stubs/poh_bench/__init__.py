"""Small benchmarking utilities for :mod:`poh`.

The original crate exposes a command line application.  Here we provide the
``benchmark_poh`` function which can be invoked manually from Python to emulate
that behaviour.
"""

from __future__ import annotations

import time
from typing import Iterable

from ..poh import ProofOfHistory


def benchmark_poh(data_stream: Iterable[bytes], iterations: int = 1) -> float:
    """Benchmark PoH verification.

    The function records ``data_stream`` into a :class:`~poh.ProofOfHistory`
    instance ``iterations`` times and measures the average duration in seconds.
    """

    start = time.perf_counter()
    for _ in range(iterations):
        poh = ProofOfHistory()
        for item in data_stream:
            poh.record(item)
        poh.verify(data_stream)
    end = time.perf_counter()
    return (end - start) / max(iterations, 1)


__all__ = ["benchmark_poh"]

