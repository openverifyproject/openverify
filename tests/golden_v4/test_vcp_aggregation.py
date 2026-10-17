"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.EXCEPTION", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_exception(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.HANDLING_MAP", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_handling_map(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.LOGICAL", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_logical(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.MEMBER_ROLE", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_member_role(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.SCORE", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_score(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.SEMANTIC", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_semantic(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.SEVERITY", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_severity(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.WEIGHT_GENERAL", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_weight_general(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.WEIGHT_IDENTITY", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_weight_identity(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.AGG.WEIGHT_SIGN_2", "test_vcp_aggregation"), ids=lambda c: c["case_id"])
def test_vcp_agg_weight_sign_2(case, request):
    run_case(case, request)
