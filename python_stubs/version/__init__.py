"""Simple version information utilities."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Version:
    major: int = 0
    minor: int = 0
    patch: int = 0
    commit: str = ""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Version({self.major}, {self.minor}, {self.patch}, commit={self.commit!r})"


def current_version() -> Version:
    """Return a :class:`Version` built from environment variables."""

    return Version(
        major=int(os.environ.get("PKG_VERSION_MAJOR", 0)),
        minor=int(os.environ.get("PKG_VERSION_MINOR", 0)),
        patch=int(os.environ.get("PKG_VERSION_PATCH", 0)),
        commit=os.environ.get("GIT_COMMIT", "")[:8],
    )


__all__ = ["Version", "current_version"]

