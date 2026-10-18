"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.DECISION.DEST", "test_vcp_decision"), ids=lambda c: c["case_id"])
def test_vcp_decision_dest(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.DECISION.ROUTE", "test_vcp_decision"), ids=lambda c: c["case_id"])
def test_vcp_decision_route(case, request):
    run_case(case, request)
