"""Lightweight helpers for tracking execution timings.

The original Rust crate collects per-program metrics during transaction
execution.  The Python translation merely stores counters and durations.  It can
be used to measure high level performance of simulated workloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict


class ExecuteTimingType(Enum):
    """High level phases of transaction execution."""

    CHECK_US = auto()
    LOAD_US = auto()
    EXECUTE_US = auto()
    STORE_US = auto()


@dataclass
class Metrics:
    """Simple metric accumulator."""

    values: Dict[ExecuteTimingType, int] = field(default_factory=dict)

    def increment(self, t: ExecuteTimingType, delta: int) -> None:
        self.values[t] = self.values.get(t, 0) + delta


@dataclass
class ProgramTiming:
    accumulated_us: int = 0
    count: int = 0

    def record(self, duration_us: int) -> None:
        self.accumulated_us += duration_us
        self.count += 1


__all__ = ["ProgramTiming", "Metrics", "ExecuteTimingType"]

