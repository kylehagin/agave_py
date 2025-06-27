"""Utility helpers for key generation."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class GrindMatch:
    starts: str
    ends: str
    count: int


def grind_parser(spec: str) -> GrindMatch:
    """Parse a grind specification ``PREFIX:SUFFIX:COUNT``."""

    parts = spec.split(":")
    if len(parts) != 3:
        raise ValueError("invalid grind spec")
    prefix, suffix, count = parts
    return GrindMatch(prefix, suffix, int(count))

