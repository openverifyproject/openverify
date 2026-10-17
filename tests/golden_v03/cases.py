"""Read frozen data and attach precise obligation links once per worker."""
import json
from functools import lru_cache
from tests.golden_v03.target import BASE


@lru_cache(maxsize=1)
def coverage_links():
    links = {}
    for row in json.loads((BASE / "coverage.json").read_text(encoding="utf-8")):
        if row["status"] == "covered":
            for identity in row["scenario_ids"]:
                links.setdefault(identity, []).append(row["requirement_id"])
    return links


def structure_cases():
    cases = [json.loads(line) for line in (BASE / "structure.jsonl").read_text(encoding="utf-8").splitlines()]
    for c in cases:
        c["feature_ids"] = coverage_links().get(c["id"], [])
    return cases


def runtime_cases():
    cases = json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
    # Same unmodified baseline trace; provenance corruptions share the normal run.
    cases = [c for c in cases if c["id"] != "master.provenance.anchors"]
    cases += json.loads((BASE / "extra-scenarios.json").read_text(encoding="utf-8"))
    for c in cases:
        c["feature_ids"] = coverage_links().get(c["id"], [])
    return cases
