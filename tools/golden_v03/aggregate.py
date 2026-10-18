"""Aggregate copied shard reports; no SUT, tests, Git, subprocesses, or network.

Usage: python -m tools.golden_v03.aggregate PATH... --output summary.json
PATH can be a JSONL file or a directory containing report JSONLs.
Only supply files belonging to the same intended campaign.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def aggregate(paths):
    files = sorted({p for path in paths for p in (path.glob("*.jsonl") if path.is_dir() else [path])})
    grouped = defaultdict(list)
    rows = defaultdict(list)
    errors = []
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["type"] == "summary":
                grouped[item["suite_name"]].append(item)
            elif item["type"] == "case":
                rows[item["suite_name"]].append(item)
    if not grouped:
        errors.append("No suite summaries found")
    suites = {}
    for suite, summaries in grouped.items():
        for summary in summaries:
            if summary.get("pytest_exitstatus"):
                errors.append(f"{suite}: pytest worker exited with {summary['pytest_exitstatus']}")
        counts = {s["shard_count"] for s in summaries}
        if len(counts) != 1:
            errors.append(suite + ": conflicting shard counts")
            continue
        count = counts.pop()
        missing_shards = sorted(set(range(count)) - {s["shard_index"] for s in summaries})
        if missing_shards:
            errors.append(f"{suite}: missing shards {missing_shards}")
        expected_sets = {tuple(s["expected_case_ids"]) for s in summaries}
        if len(expected_sets) != 1:
            errors.append(suite + ": conflicting expected inventories")
        expected = set(summaries[0]["expected_case_ids"])
        outcomes = defaultdict(list)
        for r in rows[suite]:
            outcomes[r["case_id"]].append(r["status"])
        duplicates = sorted(k for k, v in outcomes.items() if len(v) > 1)
        conflicts = sorted(k for k, v in outcomes.items() if len(set(v)) > 1)
        missing_cases = sorted(expected - outcomes.keys())
        unexpected = sorted(outcomes.keys() - expected)
        for label, values in (("duplicate case IDs", duplicates), ("conflicting outcomes", conflicts),
                              ("missing cases", missing_cases), ("unexpected cases", unexpected)):
            if values:
                errors.append(f"{suite}: {label}: {values}")
        for s in summaries:
            for case_id in s["executed_case_ids"]:
                shard = int.from_bytes(hashlib.sha256(case_id.encode()).digest(), "big") % count
                if shard != s["shard_index"]:
                    errors.append(f"{suite}: wrong shard for {case_id}")
        commits = {(s["production_commit"], s["production_source_sha256"]) for s in summaries}
        if len(commits) != 1:
            errors.append(suite + ": conflicting production implementations")
        covered = {f for r in rows[suite] if r["status"] == "passed" for f in r["obligations"]}
        expected_obligations = {f for s in summaries for f in
                                s["covered_obligations"] + s["missing_expected_obligations"]}
        missing_obligations = sorted(expected_obligations - covered)
        if missing_obligations:
            errors.append(f"{suite}: missing expected obligations: {missing_obligations}")
        suites[suite] = {"case_count": len(outcomes), "outcomes": dict(Counter(r["status"] for r in rows[suite])),
            "covered_obligations": sorted(covered), "missing_obligations": missing_obligations,
            "missing_shards": missing_shards, "duplicate_case_ids": duplicates,
            "conflicting_outcomes": conflicts, "missing_case_ids": missing_cases,
            "semantic_check_ms_sum": sum(s["semantic_check_ms"] for s in summaries),
            "relay_execution_ms_sum": sum(s["relay_execution_ms"] for s in summaries),
            "wall_duration_ms_max": max(s["elapsed_ms"] for s in summaries)}
    return {"golden_version": "0.3.0", "report_files": [str(p) for p in files],
            "suites": suites, "errors": errors, "complete": not errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = aggregate(args.paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"complete": report["complete"], "errors": report["errors"]}, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
