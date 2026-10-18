"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.EVENT.ELIGIBILITY", "test_provider_events_outcomes"), ids=lambda c: c["case_id"])
def test_provider_event_eligibility(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.EVENT.SEQUENCE", "test_provider_events_outcomes"), ids=lambda c: c["case_id"])
def test_provider_event_sequence(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.OUTCOME.SHAPE", "test_provider_events_outcomes"), ids=lambda c: c["case_id"])
def test_provider_outcome_shape(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.PROVIDER.OUTCOME.USAGE", "test_provider_events_outcomes"), ids=lambda c: c["case_id"])
def test_provider_outcome_usage(case, request):
    run_case(case, request)
