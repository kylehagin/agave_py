"""Utilities to generate C header files from small templates."""

from __future__ import annotations

import os
from typing import Mapping


def generate_headers(definitions: Mapping[str, str], out_dir: str) -> None:
    """Generate ``.h`` files from a mapping of names to contents.

    Parameters
    ----------
    definitions : Mapping[str, str]
        Mapping of header name (without extension) to header contents.
    out_dir : str
        Directory where generated files should be stored.
    """

    os.makedirs(out_dir, exist_ok=True)
    for name, content in definitions.items():
        path = os.path.join(out_dir, f"{name}.h")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)


__all__ = ["generate_headers"]

