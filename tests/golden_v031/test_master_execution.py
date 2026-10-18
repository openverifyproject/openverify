"""Test B: one canonical real Relay graph, fresh scripts and state per scenario."""
import asyncio
import os
import pytest
from tests.golden_v031.cases import runtime_cases
from tests.golden_v031.reporting import selected

CASES = runtime_cases()
if os.environ.get("GOLDEN_CASE_IDS"):
    requested = set(os.environ["GOLDEN_CASE_IDS"].split(","))
    CASES = [c for c in CASES if c["id"] in requested]
    if {c["id"] for c in CASES} != requested:
        raise ValueError("Unknown targeted runtime case ID")
CATEGORIES = sorted({c["category"] for c in CASES})


@pytest.mark.parametrize("category", CATEGORIES)
def test_master_execution(category, master_definition, report):
    from tests.golden_v031.runtime_adapter import execute, exceptional, policy_fault
    from tests.golden_v031.port_adapter import execute as port_execute
    from tests.golden_v031.availability_adapter import runtime as availability_execute
    from tests.golden_v031.ports_complete import execute as complete_port_execute
    report.inventory["MASTER EXECUTION"] = [c["id"] for c in CASES]
    report.suites.add("MASTER EXECUTION")
    for case in CASES:
        if case["category"] == category and selected(case["id"]):
            adapter = (None if case["category"] in ("availability360", "availability-role") or case["category"].startswith("ports031.")
                       else port_execute if case["category"] == "ports" else policy_fault
                       if case["category"] == "policy_fault" else execute if "scenario" in case else exceptional)
            if adapter is None:
                new_adapter = complete_port_execute if case["category"].startswith("ports031.") else availability_execute
                report.check("MASTER EXECUTION", case,
                             lambda case=case, new_adapter=new_adapter: asyncio.run(new_adapter(case, report)))
                continue
            report.check("MASTER EXECUTION", case,
                         lambda case=case, adapter=adapter: asyncio.run(adapter(case, master_definition, report)))
    report.assert_category("MASTER EXECUTION", category)
