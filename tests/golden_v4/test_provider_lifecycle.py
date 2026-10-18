"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.ATTEMPT.TRANSITION", "test_provider_lifecycle"), ids=lambda c: c["case_id"])
def test_provider_attempt_transition(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.CANCEL.ELIGIBILITY", "test_provider_lifecycle"), ids=lambda c: c["case_id"])
def test_provider_cancel_eligibility(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.DEADLINE.RACE", "test_provider_lifecycle"), ids=lambda c: c["case_id"])
def test_provider_deadline_race(case, request):
    run_case(case, request)
