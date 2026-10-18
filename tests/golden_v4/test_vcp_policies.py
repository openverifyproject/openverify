"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.POLICY.DECLARATIONS", "test_vcp_policies"), ids=lambda c: c["case_id"])
def test_vcp_policy_declarations(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.POLICY.EVAL_ORDER", "test_vcp_policies"), ids=lambda c: c["case_id"])
def test_vcp_policy_eval_order(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.POLICY.PATH", "test_vcp_policies"), ids=lambda c: c["case_id"])
def test_vcp_policy_path(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.POLICY.ROLE_RESULT", "test_vcp_policies"), ids=lambda c: c["case_id"])
def test_vcp_policy_role_result(case, request):
    run_case(case, request)
