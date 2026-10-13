"""Concrete release checks; writes only ignored root test-cache artifacts."""

import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

from openverify import parse_definition, parse_result, parse_run_record, serialize
from openverify.adapters.demo import demo_registry
from openverify.engine import Engine
from openverify.validation import validate_wire

ROOT = Path(__file__).resolve().parents[1]

valid = subprocess.run(
    ["openverify", "validate", "conformance/valid/simple-definition.json"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=True,
)
assert json.loads(valid.stdout)["valid"]
invalid = subprocess.run(
    ["openverify", "validate", "conformance/invalid/invalid-result-state.json", "--type", "result"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
assert invalid.returncode == 1
assert json.loads(invalid.stdout)["code"] == "RESULT_STATE"
for example, final in [("prose", "all"), ("generic", "envelope"), ("ai-output", "human-review")]:
    record = Engine(demo_registry()).run(
        parse_definition((ROOT / f"examples/{example}/definition.json").read_bytes()),
        json.loads((ROOT / f"examples/{example}/context.json").read_text(encoding="utf-8")),
        opportunity_id="release-verification-1",
    )
    result = record.final_results[final]
    assert result.verdict == "PASS"
    assert parse_result(serialize(result)) == result
    assert parse_run_record(serialize(record)) == record
    validate_wire("result", json.loads(serialize(result)))
    validate_wire("run-record", json.loads(serialize(record)))
    target = ROOT / ".pytest_cache" / f"{example}-run.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize(record), encoding="utf-8")
    print(f"{example}: PASS; Result/RunRecord schema and roundtrip passed")
wheel = next((ROOT / "dist").glob("*.whl"))
with zipfile.ZipFile(wheel) as archive:
    names = set(archive.namelist())
    for schema in (ROOT / "schemas/draft").glob("*.json"):
        assert f"openverify/data/schemas/{schema.name}" in names
    assert "openverify/data/profile.json" in names
    assert "openverify/py.typed" in names
print("Wheel includes all schemas, standard profile, and typing marker")
with tarfile.open(next((ROOT / "dist").glob("*.tar.gz"))) as archive:
    names = archive.getnames()
    for path in [
        "spec/draft/README.md",
        "schemas/draft/result.schema.json",
        "conformance/manifest.json",
        "profiles/standard-draft/profile.json",
        "examples/prose/definition.json",
        "tests/unit/test_values.py",
        "uv.lock",
    ]:
        assert any(name.endswith("/" + path) for name in names)
    assert not any(
        "/.venv/" in name or "/.uv-cache/" in name or name.endswith(".pyc") for name in names
    )
print("Source distribution includes specification, portable data, examples, tests, and lockfile")
print("CLI: valid accepted; invalid rejected with RESULT_STATE")
