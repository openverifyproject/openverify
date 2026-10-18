"""Source selection happens before SUT imports; timings remain enabled under -q."""
import json
import hashlib
from pathlib import Path
import sys
from time import perf_counter_ns
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.golden_v031.target import BASE, configure
from tests.golden_v031.reporting import Report

TARGET = configure()


def pytest_sessionstart(session):
    session.config._golden_v03_report = Report(TARGET)


@pytest.fixture(scope="session")
def report(request):
    return request.config._golden_v03_report


@pytest.fixture(scope="session", autouse=True)
def snapshot_integrity():
    checks = json.loads((BASE / "checksums.json").read_text(encoding="utf-8"))
    checks.update(json.loads((BASE / "checksums-extra.json").read_text(encoding="utf-8")))
    checks.update(json.loads((BASE / "checksums-coverage.json").read_text(encoding="utf-8")))
    for name, expected in checks.items():
        actual = hashlib.sha256((ROOT / name).read_text(encoding="utf-8").encode()).hexdigest()
        assert actual == expected, "Frozen Golden/specification drift: " + name


def pytest_collection_modifyitems(session, config, items):
    report = config._golden_v03_report
    if any("golden_v03/test_contract_structure.py" in item.nodeid.replace("\\", "/") for item in items):
        from tests.golden_v031.cases import structure_cases
        report.suites.add("STRUCTURE")
        report.inventory["STRUCTURE"] = [c["id"] for c in structure_cases()]
    if any("golden_v03/test_master_execution.py" in item.nodeid.replace("\\", "/") for item in items):
        from tests.golden_v031.cases import runtime_cases
        report.suites.add("MASTER EXECUTION")
        report.inventory["MASTER EXECUTION"] = [c["id"] for c in runtime_cases()]


@pytest.hookimpl(hookwrapper=True)
def pytest_collection(session):
    started = perf_counter_ns()
    yield
    session.config._golden_v03_report.phase_ns["collection"] += perf_counter_ns() - started


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()
    item.config._golden_v03_report.phase_ns[result.when] += int(result.duration * 1e9)
    if result.failed and result.when == "setup":
        report = item.config._golden_v03_report
        report.setup_errors.append({"nodeid": item.nodeid, "detail": str(result.longrepr)})
        from tests.golden_v031.cases import structure_cases, runtime_cases
        from tests.golden_v031.reporting import selected
        structure = "test_contract_structure.py" in item.nodeid
        suite = "STRUCTURE" if structure else "MASTER EXECUTION"
        category = item.callspec.params["category"]
        existing = {r["case_id"] for r in report.rows}
        for case in structure_cases() if structure else runtime_cases():
            if case["category"] == category and selected(case["id"]) and case["id"] not in existing:
                report.rows.append({"type": "case", "suite_name": suite, "case_id": case["id"],
                    "category": category, "status": "blocked", "detail": str(result.longrepr),
                    "elapsed_ms": 0, "obligations": case["feature_ids"], "applicable": True})


@pytest.fixture(scope="session")
def master_definition():
    from openverify import parse_definition
    return parse_definition((BASE / "master.json").read_text(encoding="utf-8"))


def pytest_sessionfinish(session, exitstatus):
    report = getattr(session.config, "_golden_v03_report", None)
    if report is not None:
        summaries = report.finish(session.config.pluginmanager.get_plugin("terminalreporter"), exitstatus)
        if hasattr(session.config, "workeroutput"):
            session.config.workeroutput["golden_v03_summaries"] = summaries


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    terminal = node.config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        for summary in node.workeroutput.get("golden_v03_summaries", []):
            terminal.write_sep("=", "GOLDEN v0.3.1 | " + summary["suite_name"] + " | " + summary["worker"])
            terminal.write_line(f"Cases: {summary['test_count']} | Pass: {summary['passed']} | Fail: {summary['failed']} | Duration: {summary['elapsed_ms']:.3f} ms")
            terminal.write_line(f"Relay execution: {summary['relay_execution_ms']:.3f} ms | Slowest: {summary['slowest_categories'][:1]}")
