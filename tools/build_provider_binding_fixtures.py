"""Author portable binding/provenance cases from the draft, without SDK execution."""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "conformance"
manifest = json.loads((DIRECTORY / "manifest.json").read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def case(name, kind, value, code=None, stage="semantic"):
    name = "binding-" + name
    expected = {"valid": code is None, **({"error_code": code} if code else {})}
    entry = {
        "id": name,
        "description": name.replace("-", " "),
        "object_type": kind,
        "input": f"{'invalid' if code else 'valid'}/{name}.json",
        "expected": f"expected/{name}.json",
        "stage": stage if code else "both",
        "spec": "spec/draft/provider-binding.md",
        **expected,
    }
    manifest["cases"][:] = [c for c in manifest["cases"] if c["id"] != name]
    manifest["cases"].append(entry)
    write(DIRECTORY / entry["input"], value)
    write(DIRECTORY / entry["expected"], expected)


binding = {
    "provider_id": "com.example.provider",
    "provider_version": "release-7",
    "capability_id": "com.example.execution.mock",
    "capability_version": "1",
}
case("identity", "provider-binding", binding)
bad = copy.deepcopy(binding)
bad["provider_id"] = "not_namespaced"
case("malformed-identity", "provider-binding", bad, "PROTOCOL_STRUCTURE", "schema")
bad = copy.deepcopy(binding)
del bad["provider_version"]
case("missing-version", "provider-binding", bad, "PROTOCOL_STRUCTURE", "schema")

# Reuse only the independently authored ordinary conformance dataflow snapshots.
run = json.loads((DIRECTORY / "valid/typed-complete-dataflow.json").read_text(encoding="utf-8"))
run["definition"]["graph"]["nodes"] = run["definition"]["graph"]["nodes"][:1]
run["definition"]["graph"]["edges"] = []
run["nodes"] = run["nodes"][:1]
run["final_results"] = {}
run["provider_bindings"] = {"derive": copy.deepcopy(binding)}
node = run["nodes"][0]
node["provider_binding"] = copy.deepcopy(binding)
node["executor_ref"] = binding["provider_id"]
node["executor_version"] = binding["provider_version"]
case("occurrence", "run-record", run)

for field in ("provider_id", "provider_version", "capability_id", "capability_version"):
    bad = copy.deepcopy(run)
    bad["nodes"][0]["provider_binding"][field] = "com.example.changed"
    case("changed-" + field.replace("_", "-"), "run-record", bad, "PROVENANCE_LINEAGE")
for field in ("executor_ref", "executor_version"):
    bad = copy.deepcopy(run)
    bad["nodes"][0][field] = "com.example.changed"
    case("changed-" + field.replace("_", "-"), "run-record", bad, "PROVENANCE_LINEAGE")
bad = copy.deepcopy(run)
bad["provider_bindings"] = {}
case("missing-invocation", "run-record", bad, "PROVENANCE_LINEAGE")
bad = copy.deepcopy(run)
bad["nodes"][0]["provider_binding"]["capability_id"] = "com.example.other"
bad["provider_bindings"]["derive"]["capability_id"] = "com.example.other"
case("wrong-required-capability", "run-record", bad, "PROVENANCE_LINEAGE")

rejected = copy.deepcopy(run)
node = rejected["nodes"][0]
node["state"] = "ERROR"
node["reason"] = "INVALID_PROVIDER_OUTPUT"
node["provider_output_error"] = {
    "code": "INVALID_PROVIDER_OUTPUT",
    "message": "Value violates declared capability schema",
}
node["information"] = {}
node["observation"]["usage"] = {"tokens": {"unit": "token", "kind": "EXACT", "value": 4}}
node["result"] = {
    "protocol": "draft",
    "disposition": "EXECUTED",
    "execution_outcome": "ERROR",
    "output": {
        "code": "INVALID_PROVIDER_OUTPUT",
        "message": "INVALID_PROVIDER_OUTPUT at /: Value violates declared capability schema",
    },
    "usage": {},
    "evidence": [],
}
rejected["final_results"] = {"derive": copy.deepcopy(node["result"])}
case("rejected-output-retains-usage", "run-record", rejected)
bad = copy.deepcopy(rejected)
bad["nodes"][0]["information"] = {"x": 0}
case("rejected-output-accepted", "run-record", bad, "PROVENANCE_LINEAGE")
write(DIRECTORY / "manifest.json", manifest)
