"""Persist current run evidence and exact baseline failure resolutions."""

import collections
import gzip
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from .verify_final import OUT, ROOT, rows, write


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    latest = Path((ROOT / ".pytest_cache/golden-v4/LATEST").read_text())
    current = rows(latest / "results.jsonl") + rows(OUT / "REGRESSION_RESULTS.jsonl")
    lookup = {r["case_id"]: r for r in current}
    assert len(lookup) == len(current), "Duplicate executed identities"
    old = ROOT / "conformance/golden-v4/reconciliation-v2"
    corrections = {
        c["case_id"]: c for c in json.loads((OUT / "EXPECTATION_CORRECTIONS.json").read_text())
    }
    resolved = []
    for r in rows(old / "FAILURES.jsonl"):
        identity = r["case_id"]
        if identity in corrections:
            root = (
                "HISTORICAL_WEIGHT_CATEGORY"
                if "WEIGHT_SIGN" in identity
                else "HISTORICAL_ANNOTATION"
                if "ANNOTATION" in identity
                else "HISTORICAL_AUDIT_CERTIFICATION"
            )
        elif "UNKNOWN_METHOD" in identity:
            root = "RPC_UNKNOWN_METHOD"
        elif "custom" in r["rationale"].lower():
            root = "CUSTOM_EMPTY_MEMBERSHIP"
        else:
            root = "CANCELLED_AVAILABILITY"
        actual = lookup[identity]
        assert actual["status"] == "PASS", identity
        resolved.append(
            {
                **r,
                "root_cause": root,
                "final_status": actual["status"],
                "final_expected": actual["expected"],
                "final_actual": actual["actual"],
                "expectation_revised": identity in corrections,
            }
        )
    counts = dict(collections.Counter(r["root_cause"] for r in resolved))
    assert counts == {
        "HISTORICAL_AUDIT_CERTIFICATION": 2,
        "HISTORICAL_WEIGHT_CATEGORY": 6,
        "HISTORICAL_ANNOTATION": 1,
        "CUSTOM_EMPTY_MEMBERSHIP": 10,
        "RPC_UNKNOWN_METHOD": 1,
        "CANCELLED_AVAILABILITY": 46,
    }, counts
    write(
        "ROOT_CAUSES.json",
        {
            "baseline_commit": "ad7fad6986eb79e55094687022d15a7bc70ede30",
            "baseline_failures": len(resolved),
            "counts": counts,
            "distinct_baseline_production_bugs": 3,
            "historical_expectation_corrections": len(corrections),
            "cases": resolved,
        },
    )
    checks = [r for r in current if r.get("action") == "mutation"]
    revision_mutants = [
        r
        for r in current
        if not r.get("action")
        and "MUTATION" in r["case_id"]
        and (r.get("actual") or {}).get("detected") is True
    ]
    write(
        "MUTATION_REPORT.json",
        {
            "frozen_probes": [
                {
                    "case_id": r["case_id"],
                    "status": r["status"],
                    "evidence": r.get("mutation_evidence"),
                }
                for r in checks
            ],
            "revision_probes": [
                {
                    "case_id": r["case_id"],
                    "status": r["status"],
                    "expected": r["expected"],
                    "actual": r["actual"],
                }
                for r in revision_mutants
            ],
            "detected": len(checks) + len(revision_mutants),
            "limitation": "These probes establish assertion sensitivity to these actual semantic corruptions; not exhaustive mutation coverage.",
        },
    )
    proofs = [
        {
            "proof_id": "P.FINAL.RESULT.WIRE",
            "formula": "4*4^4",
            "candidate_count": 1024,
            "valid": 66,
            "invalid": 958,
            "partition": "3*2^4 + 2^3 + 2^2 + 2 + 4",
            "test": "test_result_complete_product_and_classification[WIRE_AXIS]",
        },
        {
            "proof_id": "P.FINAL.RESULT.SEMANTIC",
            "formula": "4*3^4",
            "candidate_count": 324,
            "valid": 9,
            "invalid": 315,
            "test": "test_result_complete_product_and_classification[SEMANTIC_AXIS]",
        },
        {
            "proof_id": "P.FINAL.RESULT.OBSERVATIONS",
            "formula": "9*2^8",
            "candidate_count": 2304,
            "valid": 960,
            "invalid": 1344,
            "assumptions": "The eight actual observation names; valid payloads; judgment_schema=true. Arbitrary JSON is not enumerated.",
            "test": "test_observation_actual_names_and_complete_masks",
        },
        {
            "proof_id": "P.FINAL.GRAPH.TOPOLOGY",
            "formula": "sum(2^(n*(n-1)),n=0..4)",
            "candidate_count": 4166,
            "valid": 573,
            "invalid": 3593,
            "assumptions": "Labelled loop-free topology only; other graph constraints are separate.",
            "test": "test_small_graph_domain_and_cycles",
        },
        {
            "proof_id": "P.FINAL.HANDLING.MAPS",
            "formula": "8*2^7",
            "candidate_count": 1024,
            "assumptions": "Configuration choices only. Exceptional behavior requires separate 112 laws.",
            "test": "test_reducer_configuration_product",
        },
    ]
    schema = json.loads((ROOT / "schemas/draft/run-record.schema.json").read_text())
    for name, root in [
        ("RUN_RECORD", schema),
        ("NODE_RECORD", schema["properties"]["nodes"]["items"]),
    ]:
        n, required = len(root["properties"]), len(root["required"])
        optional = n - required
        proofs.append(
            {
                "proof_id": "P.FINAL.PRESENCE." + name,
                "formula": f"2^{n}",
                "candidate_count": 2**n,
                "valid": 2**optional,
                "invalid": 2**n - 2**optional,
                "executed_representatives": 2**optional + required,
                "saved_invalid_executions": 2**n - 2**optional - required,
                "assumptions": "Fixed valid field payloads; root object/required/properties/additionalProperties only; no root cross-key applicators. Every valid optional mask plus each single required-field deletion executed. Structural presence only, not record lineage.",
                "test": f"test_record_presence_reduction_premises[{name}]",
            }
        )
    proof_executions = {
        r["selector"].split("::")[-1]: r
        for r in current
        if r.get("assertion", {}).get("path", "").endswith("test_domain_integrity.py")
    }
    for p in proofs:
        assert proof_executions[p["test"]]["status"] == "PASS"
        p["status"] = "PROVED_STATED_PROJECTION"
        p["test_file"] = "tests/golden_v4_reconciliation/test_domain_integrity.py"
    write(
        "PROOFS.json",
        {
            "projections": proofs,
            "no_grand_candidate_total": True,
            "not_proved": [
                "Arbitrary-size DAG implementation correctness and global shared-state scheduler induction.",
                "Arbitrary JSON/schema/trace values, every public contract partition, and every platform.",
                "Unreviewed original reduction-ledger assumptions.",
            ],
        },
    )
    for name, path in [
        ("GOLDEN_RESULTS.jsonl.gz", latest / "results.jsonl"),
        ("GOLDEN_JUNIT.xml.gz", ROOT / ".pytest_cache/verification-golden.xml"),
        ("ORDINARY_JUNIT.xml.gz", ROOT / ".pytest_cache/verification-existing.xml"),
        ("REVISION_JUNIT.xml.gz", ROOT / ".pytest_cache/verification-revision.xml"),
        ("GOLDEN_STDOUT.txt.gz", ROOT / ".pytest_cache/verification-golden.log"),
        ("ORDINARY_STDOUT.txt.gz", ROOT / ".pytest_cache/verification-existing.log"),
        ("REVISION_STDOUT.txt.gz", ROOT / ".pytest_cache/verification-revision.log"),
    ]:
        with (
            path.open("rb") as source,
            (OUT / name).open("wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as target,
        ):
            shutil.copyfileobj(source, target)

    def junit(name):
        root = ET.parse(ROOT / ".pytest_cache" / name).getroot()
        suites = list(root.iter("testsuite"))
        return {
            key: sum(float(s.attrib.get(key, 0)) for s in suites)
            for key in ["tests", "failures", "errors", "skipped", "time"]
        }

    meta = json.loads((latest / "execution.json").read_text())
    modes = {}
    for mode in ["cheap", "runtime", "integration"]:
        selected = [r for r in current if r.get("execution_mode") == mode]
        modes[mode] = {
            "executed": len(selected),
            "counts": dict(collections.Counter(r["status"] for r in selected)),
            "case_duration_sum_seconds": sum(r["duration"] for r in selected),
            "note": "Partition of one complete run; duration sum is not separately measured profile wall time.",
        }
    all_failures = [r for r in current if r["status"] != "PASS"]
    (OUT / "GOLDEN_FAILURES.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in all_failures), encoding="utf-8"
    )
    source_paths = sorted(p for p in ROOT.glob("src/openverify/**/*.py"))
    write(
        "EXECUTION_REPORT.json",
        {
            "base_commit": "ad7fad6986eb79e55094687022d15a7bc70ede30",
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=ROOT, text=True
            ).strip(),
            "worktree": str(ROOT),
            "production_hashes": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
            "canonical_hashes": {
                p.name: sha(p)
                for p in (ROOT / "conformance/golden-v4/canonical-review-v2").iterdir()
                if p.is_file()
            },
            "golden": meta,
            "golden_profiles": modes,
            "ordinary": junit("verification-existing.xml"),
            "revision": json.loads((OUT / "REGRESSION_EXECUTION.json").read_text()),
            "revision_junit": junit("verification-revision.xml"),
            "mutation_probes": len(checks) + len(revision_mutants),
            "failing_case_ids": [r["case_id"] for r in all_failures],
            "certification": "NOT CERTIFIED; consult COVERAGE_REPORT.json, not passing test counts.",
        },
    )
    write(
        "ARTIFACT_SHA256.json",
        {
            p.name: sha(p)
            for p in sorted(OUT.iterdir())
            if p.is_file() and p.name != "ARTIFACT_SHA256.json"
        },
    )


if __name__ == "__main__":
    main()
