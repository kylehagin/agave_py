"""Utilities mirroring the `rayon-threadlimit` crate."""

import os
import multiprocessing


def get_thread_count() -> int:
    """Return the number of threads rayon would create."""
    env = os.getenv("SOLANA_RAYON_THREADS")
    if env is not None:
        try:
            return max(1, int(env))
        except ValueError:
            pass
    return max(1, multiprocessing.cpu_count() // 2)


def get_max_thread_count() -> int:
    """Legacy helper returning twice the thread count."""
    return get_thread_count() * 2
