"""Callback registry used by :mod:`svm` during tests."""

from typing import Any, Callable, Dict


class CallbackRegistry:
    """Register and invoke simple callback functions."""

    def __init__(self) -> None:
        self._callbacks: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        self._callbacks[name] = func

    def invoke(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name not in self._callbacks:
            raise KeyError(name)
        return self._callbacks[name](*args, **kwargs)


__all__ = ["CallbackRegistry"]
