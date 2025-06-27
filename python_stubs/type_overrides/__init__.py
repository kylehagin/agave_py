"""Wrapper modules used for test instrumentation."""

from __future__ import annotations

import random
import threading


class rand:
    randint = staticmethod(random.randint)
    random = staticmethod(random.random)


class thread:
    Thread = threading.Thread
    current_thread = staticmethod(threading.current_thread)


__all__ = ["rand", "thread"]

