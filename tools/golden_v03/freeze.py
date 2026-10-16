"""Build-only snapshot authoring. Does not import/execute OpenVerify or tests.

Run once before adapter development. Copies compact pure v0.2 data, never 12,000
test objects or runtime cases. Existing releases are immutable.
"""
from pathlib import Path
import hashlib
import json
from collections import Counter
from tools.golden_v03.expectations import master_json, master_scenarios
from tools.golden_v03.domains import (
    reducer_cases, topology_cases, policy_cases, availability_cases, guard_cases, readiness_cases, row,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "conformance/golden-v0.3"
OLD = ROOT / "conformance/golden-v0.2/versions/draft-efe9abd"
COMMIT = "5f17f402a270882f244a54dde25eda92a085eb39"


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build():
    if OUT.exists():
        raise SystemExit("Refusing to overwrite a frozen release")
    OUT.mkdir(parents=True)
    cache, cases = {}, []
    for line in (OLD / "cases.jsonl").read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        if c["operation"] not in {"parse_result", "parse_raw", "parse_object",
                                  "parse_definition", "provider_trace", "provider_object"}:
            continue
        row = {k: c[k] for k in ("id", "operation", "category", "feature_ids", "references")}
        for key, ref in (("input", c["input_ref"]), ("expected", c["expected_ref"])):
            path, pointer = ref.split("#")
            if path not in cache:
                cache[path] = json.loads((OLD / path).read_text(encoding="utf-8"))
            row[key] = cache[path][pointer[1:]]
        if row["expected"].get("blocked_error_category") and row["id"].startswith("decision."):
            row["expected"] = {"reject": True, "ambiguous_exact_code": True}
        row["mutation_witness"] = "Change the frozen acceptance/category/preserved value"
        cases.append(row)
    for factory in (reducer_cases, topology_cases, policy_cases, availability_cases, guard_cases, readiness_cases):
        cases.extend(factory())
    # Current portable normative fixtures supply newer boundaries absent in v0.2.
    for folder, provider in ((ROOT / "conformance", False), (ROOT / "provider-contract/conformance", True)):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        for c in manifest["cases"]:
            if c["object_type"] in ("stdio-session", "framing"):
                continue
            if c["object_type"] in ("lifecycle", "lifecycle-trace"):
                op = "provider_trace"
                payload = json.loads((folder / c["input"]).read_text(encoding="utf-8"))
            else:
                op = "provider_object" if provider else "parse_object"
                payload = {"object_type": c["object_type"],
                    "value": json.loads((folder / c["input"]).read_text(encoding="utf-8"))}
            exp = json.loads((folder / c["expected"]).read_text(encoding="utf-8"))
            expected = {"accept": True} if c["valid"] else {"error_code": exp["error_code"]}
            cases.append(globals()["row"]("portable." + ("provider." if provider else "vcp.") + c["id"],
                op, payload, expected, str(c["spec"]), "portable-provider" if provider else "portable-vcp"))
    (OUT / "structure.jsonl").write_text("".join(json.dumps(c, separators=(",", ":"),
        ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    write("master.json", json.loads(master_json()))
    scenarios = list(master_scenarios())
    # All scenario definitions are references to ONE immutable master, not copies.
    for c in scenarios:
        del c["scenario"]["definition"]
    write("scenarios.json", scenarios)
    sources = {}
    for folder in ("spec/draft", "provider-contract/spec/draft", "schemas/draft",
                   "provider-contract/schemas/draft"):
        for p in sorted((ROOT / folder).iterdir()):
            if p.suffix in (".md", ".json"):
                sources[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    write("metadata.json", {"golden_version": "0.3.0", "production_commit": COMMIT,
        "status": "DRAFT", "tests_run": False, "seed": 71717,
        "pure_frozen_cases": len(cases), "master_scenarios": len(scenarios),
        "categories": dict(Counter(c["category"] for c in cases)),
        "specification_sources": sources,
        "oracle_sources": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "tools/golden_v02/oracle.py", "tools/golden_v02/provider_oracle.py",
            "tools/golden_v02/compare.py", "tools/golden_v03/expectations.py", "tools/golden_v03/domains.py")}})


if __name__ == "__main__":
    build()
