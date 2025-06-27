"""Utility functions used by the installer."""

import re


def is_semver(value: str) -> bool:
    """Return ``True`` if ``value`` looks like a semantic version."""

    semver_re = re.compile(r"^\d+\.\d+\.\d+")
    return bool(semver_re.match(value))


def is_release_channel(channel: str) -> bool:
    return channel in {"edge", "beta", "stable"}


def is_explicit_release(string: str) -> bool:
    if string.startswith("v"):
        return is_semver(string[1:])
    return is_semver(string) or is_release_channel(string)

