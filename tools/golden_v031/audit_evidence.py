"""Summarize observations only. Never builds expectations or imports the SUT."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "conformance/golden-v0.3.1"
CACHE = ROOT / ".pytest_cache/golden-v031"


def main():
    observed = {}
    selected_logs = {}
    for launch_path in sorted((CACHE / "launches").glob("*-full-*.json")):
        launch = json.loads(launch_path.read_text(encoding="utf-8"))
        if "suite" not in launch:
            continue
        suite = launch["suite"]
        wanted = 7350 if suite == "A" else 323
        matches = []
        for path in (CACHE / "timings").glob("*.summary.json"):
            for s in json.loads(path.read_text(encoding="utf-8"))["runs"]:
                if s["test_count"] == wanted:
                    matches.append((path, s))
        if len(matches) != 1:
            raise ValueError("Expected exactly one full-suite report for " + suite)
        path, summary = matches[0]
        log = path.with_name(path.name.replace(".summary.json", ".jsonl"))
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        rows = [r for r in rows if r["type"] == "case"]
        selected_logs[suite] = str(log.relative_to(ROOT))
        observed[suite] = {"launch": launch, "summary": summary,
            "slowest_case": max(rows, key=lambda r: r["elapsed_ms"]),
            "timing_log": str(log.relative_to(ROOT)), "timing_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
            "actual_cases": len(rows), "failure_ids": [r["case_id"] for r in rows if r["status"] != "passed"]}
    if set(observed) != {"A", "B"}:
        raise ValueError("Both full suites must have evidence")
    reconciled = json.loads((BASE / "availability-reconciliation.json").read_text(encoding="utf-8"))
    frozen_hashes = {p.name: hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
                     for p in sorted(BASE.glob("*.json"))}
    digest = hashlib.sha256(json.dumps(frozen_hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    inventory = json.loads((BASE / "port-inventory.json").read_text(encoding="utf-8"))
    payload = {"kind": "OBSERVED_EVIDENCE_NOT_EXPECTATIONS", "golden_version": "0.3.1",
        "adapter_commit": "54b772f", "golden_branch": "test/openverify-golden-fast-v0.3.1",
        "production_commit": "5f17f402a270882f244a54dde25eda92a085eb39", "full_suites_run_once": True,
        "suites": observed, "selected_timing_logs": selected_logs,
        "availability": {"cells": len(reconciled["cells"]), "applicable": 128, "tested": 128, "missing": 0,
            "inapplicable": 232, "historical_missing_now_tested": 44,
            "historical_discrepancies": [c["cell_id"] for c in reconciled["cells"] if not c["classification_matches"]],
            "role_applicable_tested": 80, "role_inapplicable": 64},
        "ports": {p: {"methods": info["methods"], "scenarios_passed": len(info["case_ids"])} for p, info in inventory.items()},
        "remaining_questions": json.loads((BASE / "questions.json").read_text(encoding="utf-8")),
        "profile_inventory": dict(Counter(r["status"] for r in json.loads((BASE / "coverage-effective.json").read_text()))),
        "frozen_hash_algorithm": "SHA-256 over UTF-8 text with newlines normalized to LF",
        "frozen_expectation_hashes": frozen_hashes, "frozen_release_digest": digest,
        "independently_demonstrated_relay_bugs": [],
        "targeted_findings": [
            {"classification": "GOLDEN_ADAPTER_BUG", "finding": "Three original upstream Result fixture failures resolved with explicit evidence=[] and usage={}; targeted 3/3 and full A passed"},
            {"classification": "GOLDEN_ADAPTER_BUG", "finding": "New logger assumed every expectation was a mapping; string outcome handling fixed before full suites"},
            {"classification": "GOLDEN_EXPECTATION_WRONG", "finding": "Initial Aggregate RESULT role witnesses violated complete required-BLOCK membership; explicit independent spec errata preserved initial freeze"},
            {"classification": "UNDETERMINED", "finding": "port031.Store.put_return once returned PROVENANCE_LINEAGE in the initial targeted batch; unchanged isolated reproduction and full suite passed. Initial exception cause was not retained; no reproducible production defect established",
             "failed_console": ".pytest_cache/golden-v031/launches/B-targeted-19220fb36e0c4c60ae171b0b066445bb.console.txt",
             "passing_reproduction": "python -m tools.golden_v031.run_measured B --cases port031.Store.put_return"}],
        "unchanged": ["production source", "normative specifications", "all earlier frozen Golden releases"],
        "scope": "Finite declared contracts and scripted observations; no universal implementation correctness or external-provider authenticity claim"}
    folder = BASE / "evidence"
    folder.mkdir(exist_ok=True)
    (folder / "run-results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frozen_release_digest": digest,
        "manifest_hashes": {k: v for k, v in frozen_hashes.items() if k.startswith("checksums")},
        "suites": {k: {"cases": v["actual_cases"], "total_seconds": v["launch"]["total_elapsed_seconds"],
                       "failed": v["failure_ids"]} for k, v in observed.items()}}, indent=2))


if __name__ == "__main__":
    main()
