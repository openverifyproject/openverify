"""Author NEW release from independent spec tables and old immutable snapshots."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from tools.golden_v031.expectations import availability_cases, role_cases, port_cases, PORTS

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "conformance/golden-v0.3"
OUT = ROOT / "conformance/golden-v0.3.1"
HISTORY = ROOT / ".pytest_cache/golden-v02/worktree/conformance/golden-v0.2/evidence/availability-assertions.json"


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def freeze():
    if OUT.exists():
        raise SystemExit("Frozen release already exists; refusing replacement")
    OUT.mkdir()
    for path in OLD.iterdir():
        if path.is_file() and path.name != "checksums.json":
            shutil.copyfile(path, OUT / path.name)
    core, roles, ports = list(availability_cases()), list(role_cases()), list(port_cases())
    write("availability360.json", core)
    write("availability-roles.json", roles)
    write("port-scenarios.json", ports)
    historical = json.loads(HISTORY.read_text(encoding="utf-8"))
    old_cells = {(c["node_kind"], c["source"], c["availability"], c["handling"]): c for c in historical["cells"]}
    reconciled = []
    for c in core:
        h = old_cells[(c["node_kind"], c["source"], c["availability"], c["handling"])]
        reconciled.append({"cell_id": c["id"], "historical_applicable": h["runtime_applicable"],
            "current_applicable": c["runtime_applicable"], "classification_matches": h["runtime_applicable"] == c["runtime_applicable"],
            "historical_classification": h["classification"], "historical_reason": h["reason"],
            "old_witnesses": h.get("witnesses", []), "new_witness": c["id"] if c["runtime_applicable"] else None})
    write("availability-reconciliation.json", {"historical_source": HISTORY.relative_to(ROOT).as_posix(),
        "historical_sha256": hashlib.sha256(HISTORY.read_bytes()).hexdigest(), "cells": reconciled,
        "old_v03_mapping": {"CONSTANT": "CONSTANT", "RUN_INPUT": "RUN_INPUT", "EXTERNAL_REFERENCE": "EXTERNAL_REFERENCE",
            "UPSTREAM_OUTPUT": "UPSTREAM_INFORMATION for historical information-port witnesses; RESULT and DECISION are explicit role refinements",
            "UNBOUND": "No v0.3 108-cell row. Not a ValueSource. Now tested for each node kind"},
        "v03_discrepancies": "v0.3's 108 rows lacked the consumer-kind axis and UNBOUND; its constant/reference INVALID cells were isolated resolution laws for structurally invalid bindings, not legal runtime graph cells"})
    inventory = deepcopy(PORTS)
    for port_name, record in inventory.items():
        record["reference"] = ["docs/relay/architecture.md", "src/openverify/relay/ports/__init__.py"]
        record["case_ids"] = [c["id"] for c in ports if c["port"] == port_name]
        record["nonapplicable_categories"] = {
            "iteration_streaming": "Only Catalog sequence iteration, Driver report events and Transport emitted events have iteration/streaming contracts; others are single synchronous calls",
            "return_enforcement": "Void put/observe return values have no semantic channel; invalid returns do not authorize outcomes",
            "cancellation": "External task cancellation is tested at an async boundary; synchronous callbacks have no interruptible await surface"}
    write("port-inventory.json", inventory)
    write("questions.json", [
        {"id": "store.get_boundary", "status": "unsupported", "reason": "Relay.run never invokes get; get errors/invalid values are host port-contract obligations, not Relay rejection guarantees"},
        {"id": "void_port_returns", "status": "ambiguous", "reason": "Annotations require None, but no runtime rejection rule is declared for put/observe return values. Assert no semantic effect, not a fabricated error code"},
        {"id": "malicious_store_mutation", "status": "ambiguous", "reason": "No declared trust/isolation rule for a custom put mutating its argument. Do not infer one from MemoryStore behavior"},
        {"id": "sync_callback_cancelled_error", "status": "ambiguous", "reason": "No declared translation rule for a synchronous callback raising asyncio.CancelledError. Test external task cancellation instead"}])
    coverage = json.loads((OUT / "coverage.json").read_text())
    for r in coverage:
        if r["requirement_id"] in ("historical.availability360", "relay.port_fault_matrix"):
            r["status"] = "covered"
            r["suite"] = "MASTER EXECUTION"
            r["scenario_ids"] = [c["id"] for c in (core if r["requirement_id"].startswith("historical") else ports) if c.get("runtime_applicable", True)]
            r["finite_domain_or_interface_law"] = "Exact reconciled finite cells and applicable declared boundary obligations; see new inventory"
    for c in core + roles + ports:
        applicable = c.get("runtime_applicable", True)
        coverage.append({"requirement_id": c["id"], "normative_section": [c["requirement"]],
            "finite_domain_or_interface_law": c.get("reason", c.get("variant")),
            "all_declared_states": [c.get("availability", c.get("expected"))], "all_declared_transitions": None,
            "scenario_ids": [c["id"]], "suite": "MASTER EXECUTION" if applicable else "STRUCTURE",
            "independently_frozen_expectation": c.get("stimulus", {}).get("expected", c.get("expected", c["reason"] if "reason" in c else None)),
            "mutation_witness": c["mutation_witness"], "status": "covered"})
    write("coverage.json", coverage)
    metadata = json.loads((OUT / "metadata.json").read_text())
    metadata.update(golden_version="0.3.1", previous_release="golden-v0.3", previous_golden_commit="a8c91ffe3879e0da495ff5c42b2e27858b122ab5",
        core_availability_cells=len(core), core_applicable=sum(c["runtime_applicable"] for c in core),
        role_cells=len(roles), role_applicable=sum(c["runtime_applicable"] for c in roles), port_scenarios=len(ports),
        historical_classification_discrepancies=[c["cell_id"] for c in reconciled if not c["classification_matches"]],
        historical_missing=[c["cell_id"] for c in reconciled if c["historical_applicable"] and not c["old_witnesses"]],
        preserved_runtime_scenarios=55, planned_runtime_scenarios=55+sum(c["runtime_applicable"] for c in core+roles)+len(ports))
    write("metadata.json", metadata)
    write("serialization-rationale.json", {"authority": ["spec/draft/result.md", "spec/draft/wire-format.md", "spec/draft/dataflow.md", "schemas/draft/result.schema.json"],
        "wire_distinction": "Absent keys and explicit empty containers are different JSON objects. Both are permitted; no normative universal insertion/deletion equivalence is asserted",
        "fix": "Author the producer fixture with evidence=[] and usage={} explicitly; compare exact consumed snapshot. Do not normalize away keys, judgment nulls or data values",
        "original_case_ids": ["availability.UPSTREAM_RESULT.AVAILABLE." + h for h in ("BLOCK", "OMIT", "DEFAULT")]})
    files = list(OUT.iterdir()) + list((ROOT / "tools/golden_v031").glob("*.py"))
    checks = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest() for p in files if p.is_file()}
    # Preserve old independent oracle/spec anchors as well.
    checks.update({k: v for k, v in json.loads((OLD / "checksums.json").read_text()).items() if not k.startswith("conformance/golden-v0.3/")})
    write("checksums.json", checks)
    write_hash = hashlib.sha256((OUT / "checksums.json").read_bytes()).hexdigest()
    print(json.dumps({"core": len(core), "applicable": metadata["core_applicable"], "historical_missing": len(metadata["historical_missing"]),
        "role_applicable": metadata["role_applicable"], "ports": len(ports), "runtime_total": metadata["planned_runtime_scenarios"],
        "expectation_manifest_sha256": write_hash}, indent=2))


if __name__ == "__main__":
    freeze()
