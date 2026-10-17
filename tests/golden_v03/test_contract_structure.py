"""Test A: pure validation; no provider invocation or graph execution."""
import pytest
from tests.golden_v03.cases import structure_cases
from tests.golden_v03.reporting import selected

CASES = structure_cases()
CATEGORIES = sorted({c["category"] for c in CASES})


@pytest.mark.parametrize("category", CATEGORIES)
def test_contract_structure(category, report):
    from tests.golden_v03.structure_adapter import check
    report.inventory["STRUCTURE"] = [c["id"] for c in CASES]
    report.suites.add("STRUCTURE")
    for case in CASES:
        if case["category"] == category and selected(case["id"]):
            report.check("STRUCTURE", case, lambda case=case: check(case))
    report.assert_category("STRUCTURE", category)
