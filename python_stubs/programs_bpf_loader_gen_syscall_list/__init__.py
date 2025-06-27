"""Generate a simple list of system calls.

The real utility emits a JSON description of available syscalls.  For testing
purposes we merely return a static list.
"""

from __future__ import annotations


def generate_syscall_list() -> list[str]:
    """Return a list of supported syscall names."""

    # This list is purely illustrative and much shorter than the real thing.
    return [
        "log",
        "invoke",
        "sha256",
    ]


__all__ = ["generate_syscall_list"]

