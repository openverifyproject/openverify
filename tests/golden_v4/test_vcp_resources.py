"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.EXEC_OBS.PRESENCE", "test_vcp_resources"), ids=lambda c: c["case_id"])
def test_vcp_exec_obs_presence(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOURCE.PRESENCE_BINARY", "test_vcp_resources"), ids=lambda c: c["case_id"])
def test_vcp_resource_presence_binary(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOURCE.PRESENCE_TRINARY", "test_vcp_resources"), ids=lambda c: c["case_id"])
def test_vcp_resource_presence_trinary(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOURCE.RANGE_ORDER", "test_vcp_resources"), ids=lambda c: c["case_id"])
def test_vcp_resource_range_order(case, request):
    run_case(case, request)
