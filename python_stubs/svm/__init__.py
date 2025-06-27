"""Very small stack based virtual machine.

This bears no resemblance to the real SVM used by Solana other than the name.
It is purely for demonstrating how higher level components might interact with a
virtual machine implementation in tests.
"""

from typing import List


class VirtualMachine:
    """Execute simple stack based programs."""

    def __init__(self) -> None:
        self.stack: List[int] = []

    def push(self, value: int) -> None:
        self.stack.append(value)

    def add(self) -> None:
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(a + b)

    def sub(self) -> None:
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(a - b)

    def top(self) -> int:
        return self.stack[-1]


__all__ = ["VirtualMachine"]
