"""Cluster health checking utilities."""

from __future__ import annotations

import json
import urllib.request
from typing import Iterable


def check_health(urls: Iterable[str]) -> bool:
    """Return ``True`` if all given RPC ``urls`` report healthy."""

    for url in urls:
        try:
            with urllib.request.urlopen(f"{url}/health") as resp:
                status = json.loads(resp.read().decode())
                if status != "ok":
                    return False
        except Exception:
            return False
    return True


__all__ = ["check_health"]

