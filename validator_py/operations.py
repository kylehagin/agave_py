"""Operational utilities for metrics, health, and defensive rate limiting."""

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict


def setup_logging(level: int = logging.INFO) -> None:
    """Configure a simple root logger if the application has not done so."""

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


class MetricsRegistry:
    """Thread-safe counters and gauges for lightweight observability."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}

    def incr(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges)}


class RateLimiter:
    """Fixed-window rate limiter to defend against packet floods."""

    def __init__(self, limit: int, window_sec: float = 1.0):
        self.limit = limit
        self.window = window_sec
        self._arrivals: Deque[float] = deque()

    def allow(self) -> bool:
        now = time.time()
        self._arrivals.append(now)
        cutoff = now - self.window
        while self._arrivals and self._arrivals[0] < cutoff:
            self._arrivals.popleft()
        return len(self._arrivals) <= self.limit


class HealthMonitor:
    """Tracks recent activity to answer RPC health checks."""

    def __init__(
        self,
        metrics: MetricsRegistry,
        max_gossip_stall: float = 15.0,
        max_block_stall: float = 30.0,
    ):
        self.metrics = metrics
        self._max_gossip_stall = max_gossip_stall
        self._max_block_stall = max_block_stall
        now = time.time()
        self._last_gossip = now
        self._last_block = now

    def record_gossip(self) -> None:
        self._last_gossip = time.time()
        self.metrics.incr("gossip_messages")

    def record_block(self, slot: int) -> None:
        self._last_block = time.time()
        self.metrics.incr("blocks_observed")
        self.metrics.set_gauge("last_slot", float(slot))

    def record_transaction(self, accepted: bool) -> None:
        if accepted:
            self.metrics.incr("transactions_accepted")
        else:
            self.metrics.incr("transactions_rejected")

    def status(self) -> tuple[bool, str]:
        now = time.time()
        if now - self._last_gossip > self._max_gossip_stall:
            return False, "gossip stalled"
        if now - self._last_block > self._max_block_stall:
            return False, "no recent blocks"
        return True, "ok"
