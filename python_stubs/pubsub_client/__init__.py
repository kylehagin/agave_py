"""Simplified Python API for the `pubsub-client` crate."""

from dataclasses import dataclass
from typing import Optional, Callable, Any


@dataclass
class PubsubClientSubscription:
    """Represents an active subscription. Methods are placeholders."""

    operation: str
    subscription_id: int

    def send_unsubscribe(self) -> None:
        """Send an unsubscribe message (no-op)."""
        pass


class PubsubClient:
    """Blocking WebSocket RPC client placeholder."""

    @staticmethod
    def account_subscribe(url: str, pubkey: str, config: Optional[Any] = None) -> PubsubClientSubscription:
        """Subscribe to account notifications."""
        return PubsubClientSubscription(operation="accountSubscribe", subscription_id=0)

    @staticmethod
    def logs_subscribe(url: str, filter: Optional[Any] = None) -> PubsubClientSubscription:
        """Subscribe to log notifications."""
        return PubsubClientSubscription(operation="logsSubscribe", subscription_id=0)

    @staticmethod
    def slot_subscribe(url: str) -> PubsubClientSubscription:
        """Subscribe to slot notifications."""
        return PubsubClientSubscription(operation="slotSubscribe", subscription_id=0)
