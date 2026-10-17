"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.NODE.INVOKED_RESULT", "test_vcp_node_roles"), ids=lambda c: c["case_id"])
def test_vcp_node_invoked_result(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.NODE.PRIMARY", "test_vcp_node_roles"), ids=lambda c: c["case_id"])
def test_vcp_node_primary(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.NODE.ROLE", "test_vcp_node_roles"), ids=lambda c: c["case_id"])
def test_vcp_node_role(case, request):
    run_case(case, request)
