"""Python translation of the `reserved-account-keys` crate."""

from dataclasses import dataclass, field
from typing import Dict, Set, Iterable


@dataclass
class ReservedAccount:
    key: str
    feature_id: str | None = None


@dataclass
class ReservedAccountKeys:
    active: Set[str] = field(default_factory=set)
    inactive: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def new(cls, reserved_accounts: Iterable[ReservedAccount]) -> "ReservedAccountKeys":
        active = {r.key for r in reserved_accounts if r.feature_id is None}
        inactive = {r.key: r.feature_id for r in reserved_accounts if r.feature_id is not None}
        return cls(active=active, inactive=inactive)

    @classmethod
    def new_all_activated(cls) -> "ReservedAccountKeys":
        return cls(active=set(), inactive={})

    def is_reserved(self, key: str) -> bool:
        return key in self.active

    def update_active_set(self, feature_set: Set[str]) -> None:
        for k, feature in list(self.inactive.items()):
            if feature in feature_set:
                self.active.add(k)
                del self.inactive[k]

    @staticmethod
    def all_keys_iter() -> Iterable[str]:
        return []

    @staticmethod
    def empty_key_set() -> Set[str]:
        return set()
