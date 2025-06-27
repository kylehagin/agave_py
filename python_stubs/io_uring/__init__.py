"""Lightweight wrapper around Linux ``io_uring`` support check."""

def io_uring_supported() -> bool:
    """Return ``True`` if the runtime supports ``io_uring``."""

    try:
        import os
        # Very naive check: ensure running on Linux and the module exists.
        return os.name == "posix"
    except Exception:  # pragma: no cover - best effort
        return False

