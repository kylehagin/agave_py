"""Very small conformance testing helpers for :mod:`svm`."""

from . import svm  # type: ignore  # circular import is fine for stubs


def run_basic_tests() -> bool:
    """Run a tiny set of tests against the :class:`svm.VirtualMachine`."""

    vm = svm.VirtualMachine()
    vm.push(1)
    vm.push(2)
    vm.add()
    return vm.top() == 3


__all__ = ["run_basic_tests"]
