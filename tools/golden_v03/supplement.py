"""Freeze additional finite boundaries and inventory; build-only, no SUT imports."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from tools.golden_v02.oracle import schema_errors, result_error, projection
from tools.golden_v02.provider_oracle import trace_error
from tools.golden_v03.domains import row
from tools.golden_v03.extra_domains import cases as extra_cases
from tools.golden_v03.enum_coverage import coverage_rows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "conformance/golden-v0.3"


def write(name, obj):
    (BASE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def supplement():
    cases = [json.loads(line) for line in (BASE / "structure.jsonl").read_text(encoding="utf-8").splitlines()]
    # Current grammar supplies exact unsupported-feature rejection categories.
    for c in cases:
        if c["id"].startswith("mutation.") and c["id"].endswith((".expansion", ".iteration")):
            c["expected"] = {"error_code": "GRAPH_UNSUPPORTED"}
    present = {c["id"] for c in cases}
    new = list(extra_cases())
    # Check every valid categorical encoding against each observation law, beyond
    # the nine representatives' full 2^8 interaction masks.
    observations = {"judgment": None, "score": 0.5, "severity": {"domain": "opaque", "label": "x"},
        "evidence": [{"message": "known"}], "output": None,
        "usage": {"calls": {"unit": "call", "kind": "EXACT", "value": 1}},
        "metadata": {"known": True}, "extensions": []}
    for c in cases:
        if c["id"].startswith("result.axes.") and ".observation." not in c["id"] and c["expected"].get("accept"):
            for field, value in observations.items():
                payload = {**deepcopy(c["input"]), field: value}
                error = result_error(payload)
                expected = {"error_code": error} if error else {
                    "accept": True, "preserve": payload, "projection": projection(payload)}
                new.append(row(c["id"] + ".observation." + field, "parse_result", payload, expected,
                    "spec/draft/result.md", "all-valid-state-observations"))
    # Use current independent portable fixtures as seeds, normative schemas as
    # the structural oracle. No production parser constructs expected outcomes.
    seeds = {}
    for c in cases:
        if c["id"].startswith("portable.") and c["expected"].get("accept") and c["operation"] in ("parse_object", "provider_object"):
            key = (c["operation"], c["input"]["object_type"])
            seeds.setdefault(key, c)
    for (op, kind), seed in sorted(seeds.items()):
        provider = op == "provider_object"
        folder = "provider-contract/schemas/draft" if provider else "schemas/draft"
        schema = json.loads((ROOT / folder / (kind + ".schema.json")).read_text(encoding="utf-8"))
        if not isinstance(seed["input"]["value"], dict):
            continue
        for field, declaration in schema.get("properties", {}).items():
            variants = [("missing", None), ("null", None), ("object", {}), ("array", []),
                        ("number", 1), ("boolean", True), ("string", "INVALID")]
            for label, replacement in variants:
                value = deepcopy(seed["input"]["value"])
                if label == "missing":
                    value.pop(field, None)
                else:
                    value[field] = replacement
                if not schema_errors(kind, value, provider):
                    continue  # schema-valid mutations require their own semantic oracle
                code = "PROTOCOL_STRUCTURE"
                if field == "protocol" and label != "missing" and replacement != "draft":
                    code = "PROTOCOL_VERSION"
                if provider:
                    code = ("INVALID_INVOCATION" if kind == "invocation" else "PROTOCOL_VIOLATION"
                            if kind in ("cancel-request", "initialize-request") else "INVALID_PROVIDER_OUTPUT")
                    if field == "contract_version" and label != "missing":
                        code = "CONTRACT_VERSION_UNSUPPORTED"
                new.append(row(f"field.{op}.{kind}.{field}.{label}", op,
                    {"object_type": kind, "value": value}, {"error_code": code},
                    folder + "/" + kind + ".schema.json", "field-boundaries"))
    baseline = next(c["input"] for c in cases if c["id"] == "provider.completed")
    invocation = baseline["steps"][0]["invocation"]
    identity = invocation["invocation_id"]
    terminal = {"invocation_id": identity, "state": "COMPLETED", "output": {}}
    # Use matched schema's valid completed output from the trusted fixture.
    terminal = deepcopy(next(s["outcome"] for s in baseline["steps"] if s["action"] == "outcome"))
    cancel = {"invocation_id": identity}
    event = {"invocation_id": identity, "sequence": 1, "kind": "progress", "payload": {"message": "known"}}
    events = {"accept": {"action": "accept", "invocation": invocation},
              "event": {"action": "event", "event": event},
              "cancel": {"action": "cancel", "request": cancel},
              "complete": {"action": "outcome", "outcome": terminal},
              "error": {"action": "outcome", "outcome": {"invocation_id": identity, "state": "ERROR",
                        "error": {"code": "com.example.failed", "message": "known"}}},
              "cancelled": {"action": "outcome", "outcome": {"invocation_id": identity, "state": "CANCELLED"}},
              "deadline": {"action": "outcome", "outcome": {"invocation_id": identity, "state": "DEADLINE_EXCEEDED"}}}
    prefixes = {"UNSEEN": [], "RUNNING": [events["accept"]],
                "CANCEL_REQUESTED": [events["accept"], events["cancel"]],
                "TERMINAL": [events["accept"], events["complete"]]}
    for state, prefix in prefixes.items():
        for category, event_step in events.items():
            trace = deepcopy(baseline)
            trace["steps"] = deepcopy(prefix + [event_step])
            trace["finish"] = False
            error = trace_error(trace)
            new.append(row(f"transition.{state}.{category}", "provider_trace", trace,
                {"error_code": error} if error else {"accept": True},
                "provider-contract/spec/draft/lifecycle.md", "provider-transitions"))
    # Independent known record: portable fixture + explicitly trusted manifests.
    record = json.loads((ROOT / "conformance/valid/complete-run-record.json").read_text(encoding="utf-8"))
    record["provider_bindings"] = {}
    for n in record["nodes"]:
        binding = {"provider_id": "com.example.golden.p_" + n["node_id"],
                   "provider_version": "1", **n["operation"]}
        n.update(provider_binding=binding, executor_ref=binding["provider_id"], executor_version="1")
        record["provider_bindings"][n["node_id"]] = deepcopy(binding)
    write("known-record.json", record)
    new.append(row("record.known.accept", "known_record", {"mutation": None}, {"accept": True},
                   "spec/draft/provenance.md", "trusted-provenance"))
    for mutation in ("provider_version", "upstream_result", "criterion", "input", "output", "run_id",
                     "subject", "node_occurrence", "definition_id", "usage", "evidence"):
        new.append(row("record.corrupt." + mutation, "known_record", {"mutation": mutation},
                       {"reject": True}, "spec/draft/provenance.md", "trusted-provenance"))
    cases.extend(c for c in new if c["id"] not in present)
    (BASE / "structure.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False, separators=(",", ":")) + "\n" for c in cases), encoding="utf-8")
    metadata = json.loads((BASE / "metadata.json").read_text(encoding="utf-8"))
    metadata["pure_frozen_cases"] = len(cases)
    metadata["categories"] = dict(Counter(c["category"] for c in cases))
    axes = [c for c in cases if c["id"].startswith("result.axes.") and ".observation." not in c["id"]]
    metadata["categorical_results"] = {"total": len(axes),
        "valid": sum(c["expected"].get("accept", False) for c in axes),
        "invalid": sum(not c["expected"].get("accept", False) for c in axes),
        "independent_spec_count_formula": "3*2^4 + 2^3 + 2^2 + 2 + 4 = 66"}
    metadata["observation_fields"] = list(observations)
    metadata["availability_model"] = {"cells": 108, "applicable": sum(c["expected"]["applicable"] for c in cases
        if c["operation"] == "availability"), "profiles": ["CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE",
        "UPSTREAM_INFORMATION", "UPSTREAM_RESULT", "UPSTREAM_DECISION"],
        "historical_360_bound": "AMBIGUOUS: unspecified extra dimension"}
    metadata["runtime_extra_scenarios"] = 18
    metadata["planned_runtime_scenarios"] = metadata["master_scenarios"] - 1 + 18
    metadata["avoided_duplicate_runs"] = {"master.provenance.anchors": "Corruptions audited in master.normal"}
    metadata["hash_text_encoding"] = "UTF-8 with universal newlines normalized to LF"
    for group in ("specification_sources", "oracle_sources"):
        metadata[group] = {name: hashlib.sha256((ROOT / name).read_text(encoding="utf-8").encode()).hexdigest()
                           for name in metadata[group]}
    for p in sorted((ROOT / "tools/golden_v03").glob("*.py")):
        metadata["oracle_sources"][p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
    p = ROOT / "tests/golden_v03/record_oracle.py"
    metadata["oracle_sources"][p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
    write("metadata.json", metadata)
    write("implementation-sources.json", {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
          for p in sorted((ROOT / "src/openverify").rglob("*.py"))})
    inventory(cases)
    protected = [p for p in BASE.iterdir() if p.is_file() and p.name != "checksums.json"]
    protected += [ROOT / name for name in metadata["oracle_sources"]]
    protected += [ROOT / name for name in metadata["specification_sources"]]
    write("checksums.json", {p.relative_to(ROOT).as_posix(): hashlib.sha256(
          p.read_text(encoding="utf-8").encode()).hexdigest() for p in protected})


def inventory(cases):
    requirements = defaultdict(list)
    for c in cases:
        for f in c["feature_ids"]:
            requirements[f].append(c)
    coverage = []
    for identity, witnesses in sorted(requirements.items()):
        coverage.append({"requirement_id": identity, "normative_section": sorted({r for c in witnesses for r in c["references"]}),
            "finite_domain_or_interface_law": "Bounded frozen witnesses for " + identity,
            "all_declared_states": [], "all_declared_transitions": [],
            "scenario_ids": [c["id"] for c in witnesses], "suite": "STRUCTURE",
            "independently_frozen_expectation": "structure.jsonl#/expected (per scenario ID)",
            "mutation_witness": "Change acceptance, category, preserved value, resolution, or transition",
            "status": "covered", "verification": "UNVERIFIED; tests not run"})
    scenarios = json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
    extras = [{"id": "master.timeout", "category": "timeout"},
              {"id": "master.cancellation_isolation", "category": "cancellation"},
              {"id": "master.running_cancellation", "category": "cancellation"}]
    for name, code in (("catalog_failure", "CATALOG_FAILURE"), ("catalog_invalid", "CATALOG_INVALID"),
                       ("binder_failure", "BINDER_FAILURE"), ("binder_invalid", "PROVIDER_BINDING_MISMATCH"),
                       ("binder_replace", None), ("driver_replace", None), ("store_failure", None),
                       ("store_replace", None), ("observer_failure", None)):
        extra = {"id": "master.port." + name, "category": "ports"}
        if code:
            extra["error_code"] = code
        extras.append(extra)
    for role in ("ACTIVATION", "SELECTION", "ADMISSION"):
        for fault in ("exception", "provider_error"):
            extras.append({"id": f"master.policy_fault.{role}.{fault}", "category": "policy_fault",
                           "role": role, "fault": fault, "error_code": "POLICY_OUTPUT"})
    write("extra-scenarios.json", extras)
    for c in scenarios + extras:
        identity = "execution." + c["id"]
        coverage.append({"requirement_id": identity, "normative_section": [
            "spec/draft/dataflow.md", "spec/draft/lifecycle.md", "provider-contract/spec/draft/lifecycle.md"],
            "finite_domain_or_interface_law": c["id"], "all_declared_states": [], "all_declared_transitions": [],
            "scenario_ids": ["master.normal" if c["id"] == "master.provenance.anchors" else c["id"]], "suite": "MASTER EXECUTION",
            "independently_frozen_expectation": "scenarios.json#" + c["id"] if c in scenarios else "runtime-extra.json#" + c["id"],
            "mutation_witness": "Alter provider input/call count, Result, Decision, usage, or source snapshot",
            "status": "covered", "verification": "UNVERIFIED; tests not run"})
    gaps = {
        "historical.availability360": ("ambiguous", "Historical extra dimension unspecified; explicit replacement has 108 cells"),
        "decision.exact_rejection_code": ("ambiguous", "Semantic rejection asserted for seven cases; exact normative category unresolved"),
        "numeric.portable_rounding": ("ambiguous", "Exact representable boundaries and tight mathematical intervals; no portable bitwise rounding"),
        "relay.port_fault_matrix": ("uncovered", "Replacement and isolated fault witnesses exist; malicious driver/binder/catalog combinations remain in earlier profiles"),
        "integration.filesystem": ("unsupported", "Filesystem and real tool integrations excluded from fast profile"),
        "integration.process_stdio": ("unsupported", "OS process lifecycle and real stdio peers remain in Golden v0.2"),
        "integration.cli_mcp_http": ("unsupported", "Entrypoint integrations remain outside these suites"),
        "integration.large_stress": ("unsupported", "Large workload stress remains outside the bounded model"),
        "graphs.cycles_expansion_execution": ("unsupported", "Rejection checked; these constructs have no supported execution semantics"),
        "provenance.external_forgery": ("unsupported", "Known scripts anchor provider versions; no claim of external attestation"),
        "guards.general_operators": ("unsupported", "Only equality is currently supported"),
        "execution.unbounded_custom_code": ("unsupported", "All three policy roles have exception/error witnesses; arbitrary custom implementation behavior cannot be exhausted"),
        "schemas.general_implication": ("unsupported", "Only specified static primitive/finite checks and concrete runtime values"),
    }
    for identity, (status, reason) in gaps.items():
        coverage.append({"requirement_id": identity, "normative_section": ["spec/draft/open-questions.md"],
            "finite_domain_or_interface_law": reason, "all_declared_states": [], "all_declared_transitions": [],
            "scenario_ids": [], "suite": "OUTSIDE", "independently_frozen_expectation": None,
            "mutation_witness": None, "status": status})
    ambiguities = defaultdict(list)
    for c in cases:
        if c["expected"].get("spec_ambiguity"):
            ambiguities[c["expected"]["spec_ambiguity"]].append(c)
    for name, witnesses in sorted(ambiguities.items()):
        coverage.append({"requirement_id": "ambiguity." + name,
            "normative_section": sorted({r for c in witnesses for r in c["references"]}),
            "finite_domain_or_interface_law": "Semantic rejection checked; inherited exact-category ambiguity retained",
            "all_declared_states": None, "all_declared_transitions": None,
            "scenario_ids": [c["id"] for c in witnesses], "suite": "STRUCTURE",
            "independently_frozen_expectation": "Per-case allowed_error_codes in structure.jsonl",
            "mutation_witness": "Accept an invalid stimulus or return a category outside the frozen permitted alternatives",
            "status": "ambiguous"})
    # Automatically inventory every current schema enum, including nested enums.
    enums = []
    def visit(value, source, pointer=""):
        if isinstance(value, dict):
            if "enum" in value:
                enums.append({"source": source, "pointer": pointer, "all_declared_states": value["enum"]})
            for k, child in value.items():
                visit(child, source, pointer + "/" + k.replace("~", "~0").replace("/", "~1"))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                visit(child, source, pointer + "/" + str(i))
    for folder in ("schemas/draft", "provider-contract/schemas/draft"):
        for p in sorted((ROOT / folder).glob("*.json")):
            visit(json.loads(p.read_text()), p.relative_to(ROOT).as_posix())
    write("enum-inventory.json", enums)
    coverage.extend(coverage_rows(enums, cases, scenarios,
        json.loads((BASE / "master.json").read_text(encoding="utf-8"))))
    transitions = {"provider": {"states": ["UNSEEN", "RUNNING", "CANCEL_REQUESTED", "TERMINAL"],
        "events": ["accept", "event", "cancel", "complete", "error", "cancelled", "deadline"],
        "transitions": [{"case_id": c["id"], "outcome": c["expected"]} for c in cases if c["id"].startswith("transition.")]},
        "node": {"states": ["PENDING", "READY", "RUNNING", "TERMINAL"],
                 "terminal_record_states": ["SUCCESS", "ERROR", "NONEXECUTED", "CANCELLED"]}}
    write("state-transitions.json", transitions)
    for r in coverage:
        if r["requirement_id"] == "provider-transitions":
            r["all_declared_states"] = transitions["provider"]["states"]
            r["all_declared_transitions"] = transitions["provider"]["transitions"]
    write("coverage.json", coverage)
    # Every expensive scenario has a unique trace obligation. Do not equate
    # scenarios just because their final binary verdict happens to match.
    write("set-cover.json", {"scenarios_chosen": [c["id"] for c in scenarios + extras if c["id"] != "master.provenance.anchors"],
        "obligations_covered": [r["requirement_id"] for r in coverage if r["suite"] == "MASTER EXECUTION"],
        "remaining_uncovered": [r["requirement_id"] for r in coverage if r["status"] == "uncovered"],
        "duplicate_execution": [], "avoided_execution": {"master.provenance.anchors": "Same baseline trace; corruption checks folded into normal"},
        "removal_reasons": {c["id"]: "Unique stimulus and observable trace: " + c["id"]
            for c in scenarios + extras if c["id"] != "master.provenance.anchors"},
        "behavioral_minimality": "Not proven; no trace-equivalence solver"})
    write("runtime-extra.json", {"master.timeout": {"D1": "ERROR/TIMEOUT", "E2": "NONEXECUTED/INPUT_UNAVAILABLE"},
        "master.cancellation_isolation": {"cancelled_run": "all NONEXECUTED/CANCELLED", "other_run": "all SUCCESS", "run_ids": "distinct"},
        "master.running_cancellation": {"D1": "CANCELLED/CANCELLATION", "later_nodes": "NONEXECUTED/CANCELLED", "phase": "RUNNING"}})


if __name__ == "__main__":
    supplement()
