"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.INIT", "test_provider_init_invoke"), ids=lambda c: c["case_id"])
def test_provider_init(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.INVOKE.BUDGET", "test_provider_init_invoke"), ids=lambda c: c["case_id"])
def test_provider_invoke_budget(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.INVOKE.DEADLINE", "test_provider_init_invoke"), ids=lambda c: c["case_id"])
def test_provider_invoke_deadline(case, request):
    run_case(case, request)
