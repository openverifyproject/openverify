"""Portable policy/lifecycle vectors authored from prose, without SDK/engine imports."""

import copy
import json
from pathlib import Path

from dataflow_examples import constant, definition, edge, node, port

ROOT = Path(__file__).resolve().parents[1] / "conformance"
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
TIME = "2026-01-01T00:00:00Z"


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def case(name, kind, value, code=None, stage="semantic"):
    name = "policy-" + name
    folder = "invalid" if code else "valid"
    expected = {"valid": code is None, **({"error_code": code} if code else {})}
    entry = {
        "id": name,
        "description": name.replace("-", " "),
        "object_type": kind,
        "input": f"{folder}/{name}.json",
        "expected": f"expected/{name}.json",
        "stage": stage if code else "both",
        "spec": "spec/draft/execution-policy.md"
        if kind != "run-record"
        else "spec/draft/lifecycle.md",
        **expected,
    }
    manifest["cases"][:] = [c for c in manifest["cases"] if c["id"] != name]
    manifest["cases"].append(entry)
    write(ROOT / entry["input"], value)
    write(ROOT / entry["expected"], expected)


def operation():
    return {"capability_id": "com.example.policy", "capability_version": "1"}


def evaluation(role, outcome):
    return {"role": role, "input_values": {}, "input_resolutions": {}, "outcome": outcome}


def record(d, admission="RUN"):
    outcome = {"outcome": admission, "reason": "policy"}
    d = copy.deepcopy(d)
    d["execution_policy"]["admission"] = {"operation": operation()}
    return {
        "protocol": "draft",
        "run_id": "policy-fixture",
        "definition": d,
        "definition_fingerprint": "local-sha256:" + "a" * 64,
        "subject": copy.deepcopy(d["subject"]),
        "initial_context": {},
        "run_inputs": {},
        "opportunity_id": "fixture",
        "admission": outcome,
        "policy_evaluations": [
            evaluation("ACTIVATION", {"outcome": "ACTIVATE", "reason": "MANUAL"}),
            evaluation(
                "SELECTION", {"subjects": [copy.deepcopy(d["subject"])], "reason": "EXPLICIT"}
            ),
            evaluation("ADMISSION", copy.deepcopy(outcome)),
        ],
        "started_at": TIME,
        "finished_at": TIME,
        "nodes": [],
        "final_results": {},
    }


def add_node(run, n, *, disposition=None, reason=None, decision=None, state=None, observation=None):
    prior = [e["from_node"] for e in run["definition"]["graph"]["edges"] if e["to_node"] == n["id"]]
    r = {
        "node_id": n["id"],
        "kind": n["kind"],
        "operation": n["operation"],
        "upstream_node_ids": prior,
        "upstream_results": {
            k: run["final_results"][k] for k in prior if k in run["final_results"]
        },
        "input_values": {},
        "input_resolutions": {},
        "started_at": TIME,
        "finished_at": TIME,
        "usage": {},
        "state": state or ("NONEXECUTED" if disposition else "SUCCESS"),
        "information": {},
    }
    if disposition:
        r.update(
            reason=reason,
            result={
                "protocol": "draft",
                "disposition": disposition,
                "output": {"reason": reason},
                "evidence": [],
                "usage": {},
            },
        )
        run["final_results"][n["id"]] = copy.deepcopy(r["result"])
    if not disposition:
        r["observation"] = {"outputs": {}, "usage": {}, "evidence": []}
    if decision:
        r["decision"] = decision
        r["observation"]["outputs"]["decision"] = decision
    if observation:
        r["observation"] = observation
    run["nodes"].append(r)
    return r


for outcome in ("ACTIVATE", "DO_NOT_ACTIVATE"):
    case(outcome.lower(), "activation", {"outcome": outcome, "reason": "event"})
for outcome in ("RUN", "SKIP", "DEFER"):
    case(
        "admission-" + outcome.lower(),
        "admission",
        {"outcome": outcome, "reason": "resource decision"},
    )
case(
    "activation-boolean",
    "activation",
    {"outcome": False, "reason": "event"},
    "PROTOCOL_STRUCTURE",
    "schema",
)
case(
    "admission-fail",
    "admission",
    {"outcome": "FAIL", "reason": "not admission"},
    "PROTOCOL_STRUCTURE",
    "schema",
)
subject = definition([])["subject"]
case("selection-empty", "selection", {"subjects": [], "reason": "not selected"})
case("selection-subject", "selection", {"subjects": [subject], "reason": "selected"})
case(
    "selection-duplicate",
    "selection",
    {"subjects": [subject, subject], "reason": "duplicate"},
    "POLICY_OUTPUT",
)
case(
    "evaluation",
    "policy-evaluation",
    evaluation("ACTIVATION", {"outcome": "ACTIVATE", "reason": "event"}),
)
case(
    "evaluation-role-mismatch",
    "policy-evaluation",
    evaluation("ADMISSION", {"outcome": "ACTIVATE", "reason": "event"}),
    "POLICY_OUTPUT",
)
case(
    "cancellation-event",
    "cancellation-event",
    {"node_id": "a", "phase": "RUNNING", "reason": "host request"},
)

d = definition([], run_inputs=[port("x", {"type": "number"})])
p = {
    "operation": operation(),
    "inputs": [port("value", {"type": "number"})],
    "bindings": {"value": {"kind": "RUN_INPUT", "name": "x"}},
    "config": {},
    "config_schema": {"type": "object", "additionalProperties": False},
}
d["execution_policy"]["admission"] = p
case("explicit-run-input", "verification-definition", d)
for name, source, schema in (
    ("constant", constant(4), {"type": "number"}),
    ("external", {"kind": "EXTERNAL_REFERENCE", "reference": subject}, {"type": "object"}),
):
    v = copy.deepcopy(d)
    v["execution_policy"]["admission"]["inputs"][0]["schema"] = schema
    v["execution_policy"]["admission"]["bindings"]["value"] = source
    case("explicit-" + name, "verification-definition", v)
for name in ("unbound", "unknown-run", "upstream", "duplicate", "bad-config", "bad-operation"):
    v = copy.deepcopy(d)
    p = v["execution_policy"]["admission"]
    code, stage = "DATAFLOW_BINDING", "semantic"
    if name == "unbound":
        p["bindings"] = {}
    elif name == "unknown-run":
        p["bindings"]["value"]["name"] = "missing"
    elif name == "upstream":
        p["bindings"]["value"] = {"kind": "UPSTREAM_OUTPUT", "node_id": "a", "output": "x"}
    elif name == "duplicate":
        p["inputs"].append(copy.deepcopy(p["inputs"][0]))
    elif name == "bad-config":
        p["config"] = {"extra": True}
        code = "DATAFLOW_CONFIG"
    else:
        p["operation"]["capability_id"] = "bad"
        code, stage = "PROTOCOL_STRUCTURE", "schema"
    case(name, "verification-definition", v, code, stage)

nodes = [node("a", "DERIVE"), node("b", "DERIVE")]
d = definition(nodes, [edge("a", "b")])
for outcome, disposition in (("SKIP", "SKIPPED"), ("DEFER", "DEFERRED")):
    run = record(d, outcome)
    for n in nodes:
        add_node(run, n, disposition=disposition, reason="ADMISSION_" + outcome)
    case("occurrence-" + outcome.lower(), "run-record", run)
    bad = copy.deepcopy(run)
    bad["nodes"][1]["result"]["disposition"] = "CANCELLED"
    case("contradictory-" + outcome.lower(), "run-record", bad, "PROVENANCE_LINEAGE")
    if outcome == "SKIP":
        for label, index, value in (
            ("inactive-occurrence", 0, {"outcome": "DO_NOT_ACTIVATE", "reason": "absent"}),
            ("unselected-occurrence", 1, {"subjects": [], "reason": "absent"}),
            ("admission-mismatch", 2, {"outcome": "DEFER", "reason": "later"}),
        ):
            bad = copy.deepcopy(run)
            bad["policy_evaluations"][index]["outcome"] = value
            case(label, "run-record", bad, "PROVENANCE_LINEAGE")

for phase in ("BEFORE_START", "RUNNING"):
    run = record(d)
    run["cancellation"] = {"node_id": "a", "phase": phase, "reason": "host request"}
    add_node(
        run,
        nodes[0],
        disposition="CANCELLED",
        reason="CANCELLATION",
        state="CANCELLED" if phase == "RUNNING" else "NONEXECUTED",
    )
    add_node(run, nodes[1], disposition="CANCELLED", reason="CANCELLATION")
    case("cancelled-" + phase.lower(), "run-record", run)

control = node("control", "CONTROL")
d = definition([control, *nodes], [edge("control", "a"), edge("a", "b")])
for kind, disposition, reason in (
    ("CONTINUE", None, None),
    ("STOP_SUCCESS", "SKIPPED", "CONTROL_STOP"),
    ("STOP_FAILURE", "SKIPPED", "CONTROL_STOP"),
    ("DEFER", "DEFERRED", "CONTROL_DEFER"),
    ("RETRY", "SKIPPED", "RETRY_REQUESTED"),
):
    run = record(d)
    add_node(run, control, decision={"protocol": "draft", "kind": kind})
    for n in nodes:
        add_node(run, n, disposition=disposition, reason=reason)
    case("control-" + kind.lower(), "run-record", run)

d = definition([control, *nodes], [edge("control", "a"), edge("control", "b")])
run = record(d)
add_node(run, control, decision={"protocol": "draft", "kind": "ROUTE", "destination": "a"})
add_node(run, nodes[0])
add_node(run, nodes[1], disposition="SKIPPED", reason="ROUTE_EXCLUDED")
case("route-excluded", "run-record", run)

d = definition(
    nodes, [{**edge("a", "b"), "guard": {"source": constant(False), "pointer": "", "value": True}}]
)
run = record(d)
add_node(run, nodes[0])
add_node(run, nodes[1], disposition="SKIPPED", reason="GUARD_FALSE")
case("guard-false", "run-record", run)
bad = copy.deepcopy(run)
bad["nodes"][1]["reason"] = "INPUT_UNAVAILABLE"
case("wrong-lifecycle-cause", "run-record", bad, "PROVENANCE_LINEAGE")

run = record(definition([], run_inputs=[port("x", {"type": "number"})]))
bindings = {
    "value": {"kind": "RUN_INPUT", "name": "x"},
    "constant": constant(False),
    "ref": {"kind": "EXTERNAL_REFERENCE", "reference": subject},
}
run["definition"]["execution_policy"]["admission"] = {
    "operation": operation(),
    "inputs": [port("value", {"type": "number"}), port("constant"), port("ref")],
    "bindings": copy.deepcopy(bindings),
}
run["run_inputs"] = {"x": 4}
values = {"value": 4, "constant": False, "ref": subject}
run["policy_evaluations"][-1].update(
    input_values=copy.deepcopy(values),
    input_resolutions={
        name: {
            "source": bindings[name],
            "status": "AVAILABLE",
            "used_default": False,
            "value": value,
        }
        for name, value in values.items()
    },
)
case("typed-policy-provenance", "run-record", run)
bad = copy.deepcopy(run)
bad["policy_evaluations"][-1]["input_values"]["undeclared"] = 5
case("undeclared-policy-value", "run-record", bad, "PROVENANCE_LINEAGE")
bad = copy.deepcopy(run)
bad["policy_evaluations"][-1]["input_resolutions"]["value"]["value"] = 9
case("changed-policy-resolution", "run-record", bad, "PROVENANCE_LINEAGE")

write(ROOT / "manifest.json", manifest)
