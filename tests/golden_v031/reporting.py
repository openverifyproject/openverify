"""Batched per-case assertions, deterministic partitions, and portable timing."""
from collections import Counter, defaultdict
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import uuid
import traceback

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "conformance/golden-v0.3.1"


def partition():
    index = int(os.environ.get("GOLDEN_SHARD_INDEX", "0"))
    count = int(os.environ.get("GOLDEN_SHARD_COUNT", "1"))
    if count < 1 or not 0 <= index < count:
        raise ValueError("Require GOLDEN_SHARD_COUNT > 0 and 0 <= GOLDEN_SHARD_INDEX < COUNT")
    return index, count


def selected(case_id):
    index, count = partition()
    return int.from_bytes(hashlib.sha256(case_id.encode("utf-8")).digest(), "big") % count == index


class Report:
    def __init__(self, target):
        self.target = target
        self.run_id = uuid.uuid4().hex
        self.start_ns = time.perf_counter_ns()
        self.started_at = datetime.now(UTC).isoformat()
        self.rows = []
        self.relay_ns = defaultdict(int)
        self.relay_calls = defaultdict(int)
        self.phase_ns = defaultdict(int)
        self.suites = set()
        self.inventory = {}
        self.setup_errors = []
        self.progress_dir = ROOT / ".pytest_cache/golden-v031/progress"
        self.progress_dir.mkdir(parents=True, exist_ok=True)

    def check(self, suite, case, callback):
        self.suites.add(suite)
        started = time.perf_counter_ns()
        relay_started = self.relay_ns[suite]
        calls_started = self.relay_calls[suite]
        progress = self.progress_dir / (self.run_id + ".jsonl")
        if suite == "MASTER EXECUTION":
            with progress.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"event": "start", "suite": suite, "case_id": case["id"],
                    "monotonic_ns": started}) + "\n")
        status, detail, trace = "passed", None, None
        try:
            callback()
        except Exception as exc:
            status, detail = "failed", f"{type(exc).__name__}: {exc}"
            trace = traceback.format_exc()
        expectation = case.get("expected", {})
        if not isinstance(expectation, dict):
            expectation = {}
        self.rows.append({"type": "case", "suite_name": suite, "case_id": case["id"],
            "category": case["category"], "status": status, "detail": detail,
            "traceback": trace,
            "elapsed_ms": (time.perf_counter_ns() - started) / 1e6,
            "relay_execution_ms": (self.relay_ns[suite] - relay_started) / 1e6,
            "relay_calls": self.relay_calls[suite] - calls_started,
            "obligations": case.get("feature_ids", []),
            "applicable": expectation.get("applicable", True),
            "inapplicable_reason": expectation.get("reason")
                if expectation.get("applicable") is False else None})
        if suite == "MASTER EXECUTION":
            with progress.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"event": "completed", **self.rows[-1]}) + "\n")

    def assert_category(self, suite, category):
        failures = [r for r in self.rows if r["suite_name"] == suite and
                    r["category"] == category and r["status"] == "failed"]
        assert not failures, "\n".join(r["case_id"] + ": " + r["detail"] for r in failures)

    def finish(self, terminal, pytest_exitstatus):
        index, count = partition()
        directory = ROOT / ".pytest_cache/golden-v031/timings"
        directory.mkdir(parents=True, exist_ok=True)
        elapsed = (time.perf_counter_ns() - self.start_ns) / 1e6
        common = {"golden_version": "0.3.1", "run_id": self.run_id,
            "timestamp": self.started_at, "started_at": self.started_at,
            "finished_at": datetime.now(UTC).isoformat(), "elapsed_ms": elapsed,
            "worker": os.environ.get("PYTEST_XDIST_WORKER", "main"),
            "shard_index": index, "shard_count": count, "seed": 71717,
            "python": platform.python_version(), "operating_system": platform.platform(),
            "peak_memory_bytes": None, "pytest_exitstatus": int(pytest_exitstatus), **self.target}
        summaries = []
        for suite in sorted(self.suites):
            rows = [r for r in self.rows if r["suite_name"] == suite]
            categories = defaultdict(float)
            for r in rows:
                categories[r["category"]] += r["elapsed_ms"]
            counts = Counter(r["status"] for r in rows)
            manifest = json.loads((BASE / "coverage-effective.json").read_text(encoding="utf-8"))
            expected_obligations = {r["requirement_id"] for r in manifest if r["suite"] == suite
                                    and r["status"] == "covered"}
            outcomes = {r["case_id"]: r["status"] for r in rows}
            covered = sorted(r["requirement_id"] for r in manifest if r["requirement_id"] in expected_obligations
                and r["scenario_ids"] and all(outcomes.get(identity) == "passed" for identity in r["scenario_ids"]))
            summary = {"type": "summary", **common, "suite_name": suite,
                "test_count": len(rows), "obligation_count": len(expected_obligations),
                "executed_scenario_count": counts["passed"] + counts["failed"], "passed": counts["passed"],
                "failed": counts["failed"], "blocked": counts["blocked"],
                "inapplicable": sum(not r["applicable"] for r in rows),
                "failing_case_ids": [r["case_id"] for r in rows if r["status"] == "failed"],
                "blocked_case_ids": [r["case_id"] for r in rows if r["status"] == "blocked"],
                "semantic_check_ms": sum(r["elapsed_ms"] for r in rows),
                "relay_execution_ms": self.relay_ns[suite] / 1e6,
                "relay_calls": self.relay_calls[suite],
                "pytest_phase_ms": {k: v / 1e6 for k, v in self.phase_ns.items()},
                "per_category_ms": dict(categories),
                "slowest_categories": sorted(categories.items(), key=lambda x: (-x[1], x[0]))[:5],
                "covered_obligations": covered,
                "missing_expected_obligations": sorted(expected_obligations - set(covered)),
                "profile_coverage_inventory": dict(Counter(r["status"] for r in manifest)),
                "expected_case_ids": self.inventory.get(suite, []),
                "executed_case_ids": [r["case_id"] for r in rows],
                "setup_errors": self.setup_errors,
                "duration_scope": "whole pytest worker session, including collection/setup"}
            summaries.append(summary)
            if terminal:
                terminal.write_sep("=", "GOLDEN v0.3.1 | " + suite)
                terminal.write_line(f"Cases: {len(rows)} | Pass: {counts['passed']} | Fail: {counts['failed']} | Blocked: {counts['blocked']}")
                terminal.write_line(f"Total duration: {elapsed:.3f} ms | Semantic checks: {summary['semantic_check_ms']:.3f} ms")
                if suite == "MASTER EXECUTION":
                    terminal.write_line(f"Relay execution: {summary['relay_execution_ms']:.3f} ms")
                terminal.write_line(f"Obligations witnessed: {len(covered)} | Expected locally missing: {len(summary['missing_expected_obligations'])}")
                terminal.write_line("Profile inventory: " + str(summary["profile_coverage_inventory"]))
                terminal.write_line("Slowest group: " + (str(summary["slowest_categories"][0]) if categories else "none"))
        stem = f"{self.run_id}-{common['worker']}-shard-{index}-of-{count}"
        with (directory / (stem + ".jsonl")).open("x", encoding="utf-8") as stream:
            for item in [*self.rows, *summaries]:
                stream.write(json.dumps(item, ensure_ascii=False) + "\n")
        # Unique summaries avoid shared worker files. Aggregate offline across machines.
        with (directory / (stem + ".summary.json")).open("x", encoding="utf-8") as stream:
            json.dump({"runs": summaries}, stream, indent=2)
        return summaries
