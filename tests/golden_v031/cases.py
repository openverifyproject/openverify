"""Read frozen data and attach precise obligation links once per worker."""
import json
from functools import lru_cache
from tests.golden_v031.target import BASE


def cells(file):
    data = json.loads((BASE / file).read_text(encoding="utf-8"))
    corrections = json.loads((BASE / "expectation-errata.json").read_text(encoding="utf-8"))["corrections"]
    return [corrections.get(c["id"], c) for c in data]


@lru_cache(maxsize=1)
def coverage_links():
    links = {}
    for row in json.loads((BASE / "coverage-effective.json").read_text(encoding="utf-8")):
        if row["status"] == "covered":
            for identity in row["scenario_ids"]:
                links.setdefault(identity, []).append(row["requirement_id"])
    return links


def structure_cases():
    cases = [json.loads(line) for line in (BASE / "structure.jsonl").read_text(encoding="utf-8").splitlines()]
    for file in ("availability360.json", "availability-roles.json"):
        for cell in cells(file):
            cases.append({"id": cell["id"], "category": cell["category"], "operation": "availability031",
                          "input": cell, "expected": {"applicable": cell["runtime_applicable"], "reason": cell["reason"]}})
    for c in cases:
        c["feature_ids"] = coverage_links().get(c["id"], [])
    return cases


def runtime_cases():
    cases = json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
    # Same unmodified baseline trace; provenance corruptions share the normal run.
    cases = [c for c in cases if c["id"] != "master.provenance.anchors"]
    cases += json.loads((BASE / "extra-scenarios.json").read_text(encoding="utf-8"))
    for file in ("availability360.json", "availability-roles.json"):
        cases += [c for c in cells(file) if c["runtime_applicable"]]
    cases += json.loads((BASE / "port-scenarios.json").read_text(encoding="utf-8"))
    for c in cases:
        c["feature_ids"] = coverage_links().get(c["id"], [])
    return cases
