"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.AUDIT.INVENTORY", "test_inventory_coverage_gate"), ids=lambda c: c["case_id"])
def test_audit_inventory(case, request):
    run_case(case, request)
