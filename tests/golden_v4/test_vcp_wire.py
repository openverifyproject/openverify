"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.WIRE.JSON", "test_vcp_wire"), ids=lambda c: c["case_id"])
def test_wire_json(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.WIRE.ROOTS", "test_vcp_wire"), ids=lambda c: c["case_id"])
def test_wire_roots(case, request):
    run_case(case, request)
