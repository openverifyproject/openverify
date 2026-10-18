"""Explicit independently enumerated Golden v4 contract families."""
from .reporters.runner import family_cases, run_case
import pytest

@pytest.mark.parametrize("case", family_cases("V4.VCP.GUARD.BOOL", "test_vcp_schemas_guards"), ids=lambda c: c["case_id"])
def test_vcp_guard_bool(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.GUARD.OPERATOR", "test_vcp_schemas_guards"), ids=lambda c: c["case_id"])
def test_vcp_guard_operator(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.GUARD.POINTER", "test_vcp_schemas_guards"), ids=lambda c: c["case_id"])
def test_vcp_guard_pointer(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.GUARD.SOURCE", "test_vcp_schemas_guards"), ids=lambda c: c["case_id"])
def test_vcp_guard_source(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.SCHEMA.FULL", "test_vcp_schemas_guards"), ids=lambda c: c["case_id"])
def test_vcp_schema_full(case, request):
    run_case(case, request)

@pytest.mark.parametrize("case", family_cases("V4.VCP.SCHEMA.PRIMITIVE", "test_vcp_schemas_guards"), ids=lambda c: c["case_id"])
def test_vcp_schema_primitive(case, request):
    run_case(case, request)
