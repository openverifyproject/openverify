"""Test A: pure validation; no provider invocation or graph execution."""
import pytest
import os
from tests.golden_v031.cases import structure_cases
from tests.golden_v031.reporting import selected

CASES = structure_cases()
if os.environ.get("GOLDEN_CASE_IDS"):
    requested = set(os.environ["GOLDEN_CASE_IDS"].split(","))
    CASES = [c for c in CASES if c["id"] in requested]
    if {c["id"] for c in CASES} != requested:
        raise ValueError("Unknown targeted case ID")
CATEGORIES = sorted({c["category"] for c in CASES})


@pytest.mark.parametrize("category", CATEGORIES)
def test_contract_structure(category, report):
    from tests.golden_v031.structure_adapter import check
    report.inventory["STRUCTURE"] = [c["id"] for c in CASES]
    report.suites.add("STRUCTURE")
    for case in CASES:
        if case["category"] == category and selected(case["id"]):
            report.check("STRUCTURE", case, lambda case=case: check(case))
    report.assert_category("STRUCTURE", category)
