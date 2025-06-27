"""Minimal gossip network structures."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ContactInfo:
    pubkey: str
    gossip: str


class ClusterInfo:
    """Collection of peers participating in gossip."""

    def __init__(self) -> None:
        self.peers: Dict[str, ContactInfo] = {}

    def add_peer(self, info: ContactInfo) -> None:
        self.peers[info.pubkey] = info

    def all_peers(self) -> List[ContactInfo]:
        return list(self.peers.values())

