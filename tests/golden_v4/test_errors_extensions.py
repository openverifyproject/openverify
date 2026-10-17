"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.ERROR.NAMES", "test_errors_extensions"), ids=lambda c: c["case_id"])
def test_error_names(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.EXT.REQUIRED", "test_errors_extensions"), ids=lambda c: c["case_id"])
def test_vcp_ext_required(case, request):
    run_case(case, request)
