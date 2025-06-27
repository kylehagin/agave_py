"""Simplified types for the `rpc-client-api` crate."""

from dataclasses import dataclass
from typing import Any


class ErrorKind(Exception):
    pass


@dataclass
class Error(Exception):
    kind: ErrorKind
    message: str = ""


@dataclass
class Response:
    value: Any
    context: dict | None = None
