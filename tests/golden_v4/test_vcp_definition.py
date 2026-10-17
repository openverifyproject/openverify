"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.CRITERION.PRESENCE", "test_vcp_definition"), ids=lambda c: c["case_id"])
def test_vcp_criterion_presence(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.DEF.PRESENCE", "test_vcp_definition"), ids=lambda c: c["case_id"])
def test_vcp_def_presence(case, request):
    run_case(case, request)
