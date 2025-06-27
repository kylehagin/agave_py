"""Utilities to restart local validator processes for testing."""

from __future__ import annotations

import subprocess
from typing import Sequence


def restart_process(command: Sequence[str]) -> int:
    """Spawn ``command`` and return its exit code."""

    proc = subprocess.run(list(command))
    return proc.returncode


__all__ = ["restart_process"]

