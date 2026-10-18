"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.RELAY.SCHEDULER", "test_relay_cancellation_resources"), ids=lambda c: c["case_id"])
def test_relay_scheduler(case, request):
    run_case(case, request)
