"""Spec-mandated Aggregate membership correction; preserves initial frozen data.

Authority: dataflow.md: ALL upstream RESULT bindings are members; members are
required BLOCK ports. This is a Golden authoring error, not a production rule.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "conformance/golden-v0.3.1"


def main():
    output = BASE / "expectation-errata.json"
    if output.exists():
        raise SystemExit("Refusing to overwrite frozen errata")
    source = json.loads((BASE / "availability-roles.json").read_text(encoding="utf-8"))
    corrections = {}
    for c in source:
        if c["role"] != "RESULT" or c["node_kind"] != "AGGREGATE" or not c["runtime_applicable"]:
            continue
        if c["handling"] != "BLOCK":
            c["runtime_applicable"] = False
            c["static_rejection"] = "AGGREGATE_CONFIG"
            c["reason"] = "Every upstream RESULT binding is Aggregate membership. All members must be required BLOCK. Optional OMIT/DEFAULT RESULT members reject the definition"
        else:
            n = next(n for n in c["stimulus"]["definition"]["graph"]["nodes"] if n["id"] == "consumer")
            n["aggregate_inputs"] = ["data", "member"]
            n["bindings"]["members"]["value"] = ["data", "member"]
        corrections[c["id"]] = c
    output.write_text(json.dumps({"authority": "spec/draft/dataflow.md, Aggregate membership paragraphs",
        "classification": "GOLDEN_EXPECTATION_WRONG: optional supplemental RESULT bindings cannot escape membership",
        "corrections": corrections}, indent=2) + "\n", encoding="utf-8")
    revision = {"golden_version": "0.3.1", "core_cells": 360, "core_applicable": 128, "core_inapplicable": 232,
        "role_cells": 144, "role_applicable": 80, "role_inapplicable": 64,
        "pure_cases": 7350, "preserved_runtime_scenarios": 55, "new_port_scenarios": 60,
        "runtime_scenarios": 323, "initial_freeze_commit": "c1dd9b7",
        "overlay": output.name, "remaining_questions": "questions.json"}
    path = BASE / "revision.json"
    path.write_text(json.dumps(revision, indent=2) + "\n", encoding="utf-8")
    checks = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
              for p in (output, path, Path(__file__).resolve())}
    (BASE / "checksums-extra.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
