"""Minimal translation of the ``feature-set`` crate."""

from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class FeatureSet:
    """Tracks active and inactive feature identifiers."""

    active: Dict[str, int] = field(default_factory=dict)
    inactive: Set[str] = field(default_factory=set)

    def is_active(self, feature_id: str) -> bool:
        return feature_id in self.active

    def activate(self, feature_id: str, slot: int) -> None:
        self.inactive.discard(feature_id)
        self.active[feature_id] = slot

    def deactivate(self, feature_id: str) -> None:
        self.active.pop(feature_id, None)
        self.inactive.add(feature_id)

