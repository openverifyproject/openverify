"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.GRAPH.DAG_0_4", "test_vcp_graph_structure"), ids=lambda c: c["case_id"])
def test_vcp_graph_dag_0_4(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.GRAPH.DEFINITION", "test_vcp_graph_structure"), ids=lambda c: c["case_id"])
def test_vcp_graph_definition(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.GRAPH.FEATURES", "test_vcp_graph_structure"), ids=lambda c: c["case_id"])
def test_vcp_graph_features(case, request):
    run_case(case, request)
