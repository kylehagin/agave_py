"""Utilities for parsing benchmark performance results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Tuple


def parse_bench_results(path: str | Path) -> Dict[str, Tuple[int, int]]:
    """Parse a file containing JSON benchmark results.

    Parameters
    ----------
    path:
        Path to a file containing one JSON object per line.  Objects with the
        key ``"type": "bench"`` are considered.

    Returns
    -------
    dict
        Mapping benchmark name to ``(median, deviation)`` integer tuples.
    """

    results: Dict[str, Tuple[int, int]] = {}
    with Path(path).open("r") as fh:
        for line in fh:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if data.get("type") != "bench":
                continue
            name = str(data.get("name", "")).strip('"')
            median = int(data.get("median", 0))
            deviation = int(data.get("deviation", 0))
            results[name] = (median, deviation)
    return results


__all__ = ["parse_bench_results"]

