import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from python_stubs.compute_budget_instruction import ComputeBudgetInstructionDetails
from python_stubs.compute_budget import ComputeBudgetLimits

COMPUTE_BUDGET = "compute_budget"

def cu_limit(val: int):
    return (COMPUTE_BUDGET, b"\x01" + val.to_bytes(4, "little"))

def cu_price(val: int):
    return (COMPUTE_BUDGET, b"\x02" + val.to_bytes(8, "little"))

def test_try_from_parses_instructions():
    instructions = [
        ("other", b"\x00"),
        cu_limit(5),
        cu_price(9),
    ]
    details = ComputeBudgetInstructionDetails.try_from(instructions)
    assert details.requested_compute_unit_limit == (1, 5)
    assert details.requested_compute_unit_price == (2, 9)

def test_try_from_duplicate_error():
    instructions = [
        cu_limit(1),
        cu_limit(2),
    ]
    with pytest.raises(ValueError):
        ComputeBudgetInstructionDetails.try_from(instructions)

def test_sanitize_and_convert():
    details = ComputeBudgetInstructionDetails.try_from([cu_limit(7), cu_price(3)])
    limits = details.sanitize_and_convert_to_compute_budget_limits(None)
    assert isinstance(limits, ComputeBudgetLimits)
    assert limits.compute_unit_limit == 7
    assert limits.compute_unit_price == 3
