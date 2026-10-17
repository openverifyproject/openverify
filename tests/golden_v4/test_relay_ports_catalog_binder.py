"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.RELAY.PORTS", "test_relay_ports_catalog_binder"), ids=lambda c: c["case_id"])
def test_relay_ports(case, request):
    run_case(case, request)
