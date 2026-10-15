"""Read-only integrity, independence, coverage-link and fixture audit."""

from __future__ import annotations

import ast
import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def baseline():
    index = json.loads((ROOT / "conformance/golden-v0.2/manifest.json").read_text(encoding="utf-8"))
    return ROOT / "conformance/golden-v0.2" / index["current"]


@lru_cache(maxsize=128)
def _read_bundle(path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(reference: str):
    name, pointer = reference.split("#", 1)
    path = (baseline() / name).resolve()
    if not path.is_relative_to(baseline().resolve()):
        raise AssertionError("fixture path escapes baseline")
    obj = _read_bundle(path)
    for segment in pointer.split("/")[1:]:
        obj = obj[segment.replace("~1", "/").replace("~0", "~")]
    return obj


def cases():
    return [
        json.loads(line)
        for line in (baseline() / "cases.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def verify():
    from tools.golden_v02.oracle import result_error, schema_errors
    from tools.golden_v02.provider_oracle import trace_error
    from tools.golden_v02.enumerate_graphs import generated, labeled_dags
    from tools.golden_v02.compare import equal

    base = baseline()
    checks = json.loads((base / "checksum-manifest.json").read_text(encoding="utf-8"))["files"]
    for name, expected in checks.items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, "hash mismatch: " + name
    snapshot = json.loads((base / "specification-snapshot.json").read_text(encoding="utf-8"))
    for name, expected in snapshot["sources"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, (
            "specification drift: " + name
        )
    all_cases = cases()
    identities = [c["id"] for c in all_cases]
    assert len(identities) == len(set(identities)), "duplicate case IDs"
    assert len(all_cases) == json.loads((base / "manifest.json").read_text())["case_count"]
    features = {f["feature_id"]: f for f in json.loads((base / "feature-matrix.json").read_text())}
    referenced = set()
    for case in all_cases:
        payload = resolve(case["input_ref"])
        expected = resolve(case["expected_ref"])
        for key in ("input_ref", "expected_ref"):
            referenced.add(key and case[key].split("#")[0])
        for f in case["feature_ids"]:
            assert f in features, (case["id"], f)
            assert case["id"] in features[f]["valid_case_ids"] + features[f]["invalid_case_ids"]
        if case["operation"] == "parse_result":
            equal(expected.get("error_code"), result_error(payload), case["id"])
        if case["operation"] == "provider_trace":
            if expected.get("allowed_error_codes"):
                assert trace_error(payload) in expected["allowed_error_codes"], case["id"]
            else:
                equal(expected.get("error_code"), trace_error(payload), case["id"])
        if case["operation"] == "parse_definition" and expected.get("accept"):
            assert not schema_errors("verification-definition", payload), case["id"]
        if case["operation"] in ("run", "metamorphic_run", "policy_run"):
            assert not schema_errors("verification-definition", payload["definition"]), case["id"]
    for folder in ("fixtures", "expected"):
        files = {p.relative_to(base).as_posix() for p in (base / folder).rglob("*.json")}
        assert files <= referenced, "orphan fixture files: " + str(files - referenced)
        for path in (base / folder).rglob("*.json"):
            # Every bundle entry must be a case, not merely every bundle file.
            data = json.loads(path.read_text(encoding="utf-8"))
            assert set(data) <= set(identities), "orphan bundle entries: " + str(path)
    from tools.golden_v02.oracle import strict_loads

    for path in base.rglob("*.json"):
        strict_loads(path.read_bytes())
    for name in json.loads((base / "manifest.json").read_text())["oracle_source_hashes"]:
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                assert not any(a.name.startswith("openverify") for a in n.names), name
            elif isinstance(n, ast.ImportFrom):
                assert not (n.module or "").startswith("openverify"), name
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                assert n.func.id not in ("eval", "exec", "__import__"), name
    equal(
        json.loads(json.dumps(list(generated(71717)))),
        json.loads(json.dumps(list(generated(71717)))),
    )
    assert len(list(labeled_dags(4))) == 573
    supported = [f for f in features.values() if f["normative_support"] == "supported"]
    uncovered = [
        f["feature_id"] for f in supported if not f["valid_case_ids"] and not f["invalid_case_ids"]
    ]
    return {
        "integrity": "PASS",
        "unique_cases": len(all_cases),
        "spec_files": len(snapshot["sources"]),
        "hash_checked_files": len(checks),
        "uncovered_feature_ids": uncovered,
        "sut_executed": False,
        "scope": "fixture integrity and independently generated tables; not implementation conformance",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
