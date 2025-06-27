"""Transaction types for the :mod:`svm` stub."""

from dataclasses import dataclass


@dataclass
class SVMTransaction:
    program: str
    data: bytes

    def execute(self, vm) -> None:
        # In reality this would serialize instructions.  Here we just push bytes
        # onto the VM stack as integers.
        for b in self.data:
            vm.push(b)


__all__ = ["SVMTransaction"]
