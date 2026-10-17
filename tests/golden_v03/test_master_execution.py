"""Test B: one canonical real Relay graph, fresh scripts and state per scenario."""
import asyncio
import pytest
from tests.golden_v03.cases import runtime_cases
from tests.golden_v03.reporting import selected

CASES = runtime_cases()
CATEGORIES = sorted({c["category"] for c in CASES})


@pytest.mark.parametrize("category", CATEGORIES)
def test_master_execution(category, master_definition, report):
    from tests.golden_v03.runtime_adapter import execute, exceptional, policy_fault
    from tests.golden_v03.port_adapter import execute as port_execute
    report.inventory["MASTER EXECUTION"] = [c["id"] for c in CASES]
    report.suites.add("MASTER EXECUTION")
    for case in CASES:
        if case["category"] == category and selected(case["id"]):
            adapter = (port_execute if case["category"] == "ports" else policy_fault
                       if case["category"] == "policy_fault" else execute if "scenario" in case else exceptional)
            report.check("MASTER EXECUTION", case,
                         lambda case=case, adapter=adapter: asyncio.run(adapter(case, master_definition, report)))
    report.assert_category("MASTER EXECUTION", category)
