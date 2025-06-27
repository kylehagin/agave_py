"""Simplified API mirroring the `remote-wallet` crate."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RemoteWalletInfo:
    pubkey: str
    path: str


@dataclass
class Device:
    path: str
    pubkey: str


class RemoteWalletManager:
    """Placeholder manager for hardware wallets."""

    def __init__(self) -> None:
        self.devices: List[Device] = []

    def update_devices(self) -> int:
        """Scan and update available devices. Returns the count."""
        return len(self.devices)

    def list_devices(self) -> List[RemoteWalletInfo]:
        """Return information about connected devices."""
        return [RemoteWalletInfo(d.pubkey, d.path) for d in self.devices]

    def get_wallet_info(self, pubkey: str) -> Optional[RemoteWalletInfo]:
        for dev in self.devices:
            if dev.pubkey == pubkey:
                return RemoteWalletInfo(dev.pubkey, dev.path)
        return None
