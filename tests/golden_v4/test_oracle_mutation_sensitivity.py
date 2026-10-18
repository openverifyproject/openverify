"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.AUDIT.MUTATION", "test_oracle_mutation_sensitivity"), ids=lambda c: c["case_id"])
def test_audit_mutation(case, request):
    run_case(case, request)
