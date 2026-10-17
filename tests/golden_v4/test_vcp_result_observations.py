"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESULT.OBS_MASK", "test_vcp_result_observations"), ids=lambda c: c["case_id"])
def test_vcp_result_obs_mask(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESULT.VALUES", "test_vcp_result_observations"), ids=lambda c: c["case_id"])
def test_vcp_result_values(case, request):
    run_case(case, request)
