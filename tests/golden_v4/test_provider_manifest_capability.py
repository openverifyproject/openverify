"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.FEATURE_FLAGS", "test_provider_manifest_capability"), ids=lambda c: c["case_id"])
def test_provider_feature_flags(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.VCP_COMPAT", "test_provider_manifest_capability"), ids=lambda c: c["case_id"])
def test_provider_vcp_compat(case, request):
    run_case(case, request)
