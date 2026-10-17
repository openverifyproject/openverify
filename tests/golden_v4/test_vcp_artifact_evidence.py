"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.ARTIFACT.PRESENCE", "test_vcp_artifact_evidence"), ids=lambda c: c["case_id"])
def test_vcp_artifact_presence(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.EVIDENCE.MEANING", "test_vcp_artifact_evidence"), ids=lambda c: c["case_id"])
def test_vcp_evidence_meaning(case, request):
    run_case(case, request)
