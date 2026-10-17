"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.CANCEL.ELIGIBILITY", "test_vcp_lifecycle_cancel"), ids=lambda c: c["case_id"])
def test_vcp_cancel_eligibility(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.LIFECYCLE.PHASES", "test_vcp_lifecycle_cancel"), ids=lambda c: c["case_id"])
def test_vcp_lifecycle_phases(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.LIFECYCLE.REASON", "test_vcp_lifecycle_cancel"), ids=lambda c: c["case_id"])
def test_vcp_lifecycle_reason(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.LIFECYCLE.RESULT", "test_vcp_lifecycle_cancel"), ids=lambda c: c["case_id"])
def test_vcp_lifecycle_result(case, request):
    run_case(case, request)
