"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.NODE_RECORD.PRESENCE", "test_vcp_records"), ids=lambda c: c["case_id"])
def test_vcp_node_record_presence(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RECORD.LINEAGE", "test_vcp_records"), ids=lambda c: c["case_id"])
def test_vcp_record_lineage(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.RUN_RECORD.PRESENCE", "test_vcp_records"), ids=lambda c: c["case_id"])
def test_vcp_run_record_presence(case, request):
    run_case(case, request)
