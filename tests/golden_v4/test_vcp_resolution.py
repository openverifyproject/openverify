"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOLVE.CONSUMER", "test_vcp_resolution"), ids=lambda c: c["case_id"])
def test_vcp_resolve_consumer(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOLVE.HANDLER", "test_vcp_resolution"), ids=lambda c: c["case_id"])
def test_vcp_resolve_handler(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOLVE.RAW", "test_vcp_resolution"), ids=lambda c: c["case_id"])
def test_vcp_resolve_raw(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOLVE.RECORD_BITS", "test_vcp_resolution"), ids=lambda c: c["case_id"])
def test_vcp_resolve_record_bits(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RESOLVE.UNBOUND", "test_vcp_resolution"), ids=lambda c: c["case_id"])
def test_vcp_resolve_unbound(case, request):
    run_case(case, request)
