"""Feature flags used by the :mod:`svm` stub."""

from dataclasses import dataclass
from typing import Set


@dataclass
class FeatureSet:
    """A collection of enabled feature names."""

    features: Set[str]

    def is_active(self, name: str) -> bool:
        return name in self.features


__all__ = ["FeatureSet"]
