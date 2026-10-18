"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESULT.PROJECTION", "test_vcp_result_axes"), ids=lambda c: c["case_id"])
def test_vcp_result_projection(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESULT.SEMANTIC_AXIS", "test_vcp_result_axes"), ids=lambda c: c["case_id"])
def test_vcp_result_semantic_axis(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESULT.WIRE_AXIS", "test_vcp_result_axes"), ids=lambda c: c["case_id"])
def test_vcp_result_wire_axis(case, request):
    run_case(case, request)
