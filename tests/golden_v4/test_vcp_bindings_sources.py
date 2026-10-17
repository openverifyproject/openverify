"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.BIND.IDENTITY", "test_vcp_bindings_sources"), ids=lambda c: c["case_id"])
def test_vcp_bind_identity(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.PORT.DEFAULT", "test_vcp_bindings_sources"), ids=lambda c: c["case_id"])
def test_vcp_port_default(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.PORT.HANDLING", "test_vcp_bindings_sources"), ids=lambda c: c["case_id"])
def test_vcp_port_handling(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.SOURCE.KIND", "test_vcp_bindings_sources"), ids=lambda c: c["case_id"])
def test_vcp_source_kind(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.SOURCE.POLICY", "test_vcp_bindings_sources"), ids=lambda c: c["case_id"])
def test_vcp_source_policy(case, request):
    run_case(case, request)
