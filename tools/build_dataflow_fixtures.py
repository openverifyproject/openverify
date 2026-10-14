"""Portable typed-dataflow cases, authored from spec/draft/dataflow.md, without SDK use."""

import copy
import json
from pathlib import Path

from dataflow_examples import constant, definition, edge, information, node, port, upstream

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "conformance"
manifest = json.loads((DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
cases = manifest["cases"]


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def case(name, kind, value, code=None, stage="semantic"):
    folder = "invalid" if code else "valid"
    expected = {"valid": code is None, **({"error_code": code} if code else {})}
    entry = {
        "id": name,
        "description": name.replace("-", " "),
        "object_type": kind,
        "input": f"{folder}/{name}.json",
        "expected": f"expected/{name}.json",
        "stage": stage if code else "both",
        "spec": "spec/draft/dataflow.md",
        **expected,
    }
    cases[:] = [c for c in cases if c["id"] != name]
    cases.append(entry)
    write(DIRECTORY / entry["input"], value)
    write(DIRECTORY / entry["expected"], expected)


PASS = {
    "protocol": "draft",
    "disposition": "EXECUTED",
    "execution_outcome": "SUCCESS",
    "applicability": "APPLICABLE",
    "determination": "KNOWN",
    "verdict": "PASS",
    "evidence": [],
    "usage": {},
}
TIME = "2026-01-01T00:00:00Z"
HANDLING = dict.fromkeys(
    ["UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING"], "REJECT"
)


def run_record(d, supplied, observations, disabled=()):
    """Build transparent static snapshots; observers supply every produced value."""
    records, final = {}, {}
    for n in d["graph"]["nodes"]:
        values, resolutions, blocked = {}, {}, False
        for p in n["inputs"]:
            source = n["bindings"].get(p["name"])
            status, available, value = "ABSENT", False, None
            if source:
                kind = source["kind"]
                if kind == "CONSTANT":
                    value, available = source["value"], True
                elif kind == "EXTERNAL_REFERENCE":
                    value, available = source["reference"], True
                elif kind == "RUN_INPUT":
                    if source["name"] in supplied:
                        value, available = supplied[source["name"]], True
                else:
                    producer = records[source["node_id"]]
                    if source["output"] == "result" and producer["kind"] in (
                        "EVALUATE",
                        "AGGREGATE",
                    ):
                        value, available = producer["result"], True
                    elif source["output"] in producer["information"]:
                        value, available = producer["information"][source["output"]], True
                    elif producer["state"] == "NONEXECUTED":
                        status = "PRODUCER_NOT_EXECUTED"
                    elif producer["state"] == "ERROR":
                        status = "PRODUCER_ERROR"
                    else:
                        status = "OUTPUT_MISSING"
            resolution = {"status": "AVAILABLE" if available else status, "used_default": False}
            if source:
                resolution["source"] = copy.deepcopy(source)
            if available:
                resolution["value"] = copy.deepcopy(value)
                values[p["name"]] = copy.deepcopy(value)
            elif p["on_unavailable"] == "DEFAULT":
                resolution.update(used_default=True, value=copy.deepcopy(p["default"]["value"]))
                values[p["name"]] = copy.deepcopy(p["default"]["value"])
            elif p["required"]:
                blocked = True
            resolutions[p["name"]] = resolution
        prior = [e["from_node"] for e in d["graph"]["edges"] if e["to_node"] == n["id"]]
        r = {
            "node_id": n["id"],
            "kind": n["kind"],
            "operation": n["operation"],
            "upstream_node_ids": prior,
            "upstream_results": {k: final[k] for k in prior if k in final},
            "input_values": values,
            "input_resolutions": resolutions,
            "started_at": TIME,
            "finished_at": TIME,
            "usage": {"wall_time": {"unit": "s", "kind": "EXACT", "value": 0}},
            "state": "SUCCESS",
            "information": {},
        }
        if blocked or n["id"] in disabled:
            reason = "ADMISSION_SKIP" if n["id"] in disabled else "INPUT_UNAVAILABLE"
            r.update(
                state="NONEXECUTED",
                reason=reason,
                result={
                    "protocol": "draft",
                    "disposition": "SKIPPED",
                    "output": {"reason": reason},
                    "evidence": [],
                    "usage": {},
                },
            )
        else:
            obs = copy.deepcopy(observations[n["id"]])
            obs.setdefault("usage", {})
            obs.setdefault("evidence", [])
            r["observation"] = obs
            if "error" in obs:
                error = obs["error"]
                r.update(
                    state="ERROR",
                    reason=error["code"],
                    result={
                        "protocol": "draft",
                        "disposition": "EXECUTED",
                        "execution_outcome": "ERROR",
                        "output": {
                            "code": error["code"],
                            "message": error["code"] + " at /: " + error["message"],
                        },
                        "evidence": [],
                        "usage": {},
                    },
                )
            else:
                for p in n["outputs"]:
                    if p["role"] == "INFORMATION":
                        r["information"][p["name"]] = obs["outputs"][p["name"]]
                    else:
                        r[p["role"].lower()] = obs["outputs"][p["name"]]
        if "result" in r:
            final[n["id"]] = r["result"]
        records[n["id"]] = r
    return {
        "protocol": "draft",
        "run_id": "typed-fixture",
        "definition": copy.deepcopy(d),
        "definition_fingerprint": "local-sha256:" + "a" * 64,
        "subject": copy.deepcopy(d["subject"]),
        "initial_context": {},
        "run_inputs": copy.deepcopy(supplied),
        "opportunity_id": "fixture",
        "admission": {"outcome": "RUN", "reason": "ALWAYS"},
        "policy_evaluations": [
            {
                "role": "ACTIVATION",
                "input_values": {},
                "input_resolutions": {},
                "outcome": {"outcome": "ACTIVATE", "reason": "MANUAL"},
            },
            {
                "role": "SELECTION",
                "input_values": {},
                "input_resolutions": {},
                "outcome": {"subjects": [copy.deepcopy(d["subject"])], "reason": "EXPLICIT"},
            },
            {
                "role": "ADMISSION",
                "input_values": {},
                "input_resolutions": {},
                "outcome": {"outcome": "RUN", "reason": "ALWAYS"},
            },
        ],
        "started_at": TIME,
        "finished_at": TIME,
        "nodes": list(records.values()),
        "final_results": final,
    }


d = definition(
    [
        node(
            "derive",
            "DERIVE",
            inputs=[port("x", {"type": "integer"})],
            outputs=[information("x", {"type": "integer"})],
            bindings={"x": {"kind": "RUN_INPUT", "name": "x"}},
        ),
        node(
            "judge",
            "EVALUATE",
            inputs=[port("x", {"type": "integer"})],
            bindings={"x": upstream("derive", "x")},
        ),
        node(
            "control",
            "CONTROL",
            inputs=[port("check", {"type": "object"})],
            bindings={"check": upstream("judge")},
        ),
        node(
            "other",
            "DERIVE",
            inputs=[port("x", {"type": "integer"})],
            outputs=[information("copy", {"type": "integer"})],
            bindings={"x": upstream("derive", "x")},
        ),
    ],
    [edge("derive", "judge"), edge("judge", "control"), edge("derive", "other")],
    [port("x", {"type": "integer"})],
)
obs = {
    "derive": {"outputs": {"x": 0}},
    "judge": {"outputs": {"result": PASS}},
    "control": {"outputs": {"decision": {"protocol": "draft", "kind": "CONTINUE"}}},
    "other": {"outputs": {"copy": 0}},
}
run = run_record(d, {"x": 0}, obs)
case("typed-complete-dataflow", "run-record", run)
case("typed-run-input-derive", "verification-definition", d)
case("typed-multiple-consumers", "graph", d["graph"])
case("typed-operation", "operation-requirement", d["graph"]["nodes"][0]["operation"])
case("typed-information-port", "output-port", information("x", {"type": "integer"}))
case("typed-input-port", "input-port", port("x", {"type": "integer"}))
case("typed-value-source", "value-source", constant(None))
case(
    "typed-observation",
    "execution-observation",
    {"outputs": {"x": False}, "usage": {}, "evidence": []},
)
case(
    "typed-resolution",
    "input-resolution",
    {"source": constant(None), "status": "AVAILABLE", "used_default": False, "value": None},
)
for value, label in [
    (None, "null"),
    (False, "false"),
    (0, "zero"),
    (0.0, "float-zero"),
    ("", "empty-string"),
    ([], "empty-array"),
    ({}, "empty-object"),
]:
    n = node(
        "constant",
        "DERIVE",
        inputs=[port("value")],
        outputs=[information("value")],
        bindings={"value": constant(value)},
    )
    r = run_record(definition([n]), {}, {"constant": {"outputs": {"value": value}}})
    case("typed-constant-" + label, "run-record", r)
ref = {"id": "document", "type": "application/json", "locator": {"opaque": False}}
n = node(
    "reference",
    "DERIVE",
    inputs=[port("ref", {"type": "object"})],
    bindings={"ref": {"kind": "EXTERNAL_REFERENCE", "reference": ref}},
)
case(
    "typed-external-reference",
    "run-record",
    run_record(definition([n]), {}, {"reference": {"outputs": {}}}),
)
n = node(
    "optional",
    "DERIVE",
    inputs=[
        port("omitted", required=False),
        port("defaulted", required=False, default=constant(None)),
    ],
)
case(
    "typed-optional-absence-default",
    "run-record",
    run_record(definition([n]), {}, {"optional": {"outputs": {}}}),
)
case(
    "typed-independent-nodes",
    "verification-definition",
    definition([node("a", "DERIVE"), node("b", "DERIVE")]),
)
for name, change, code in [
    ("unbound", lambda x: x["graph"]["nodes"][0]["bindings"].clear(), "DATAFLOW_BINDING"),
    (
        "unknown-run-input",
        lambda x: x["graph"]["nodes"][0]["bindings"]["x"].update(name="absent"),
        "DATAFLOW_BINDING",
    ),
    (
        "unknown-producer",
        lambda x: x["graph"]["nodes"][1]["bindings"]["x"].update(node_id="absent"),
        "DATAFLOW_BINDING",
    ),
    (
        "unknown-output",
        lambda x: x["graph"]["nodes"][1]["bindings"]["x"].update(output="absent"),
        "DATAFLOW_BINDING",
    ),
    (
        "unknown-target",
        lambda x: x["graph"]["nodes"][0]["bindings"].update(absent=constant(0)),
        "DATAFLOW_BINDING",
    ),
    ("forward-without-dependency", lambda x: x["graph"]["edges"].pop(0), "DATAFLOW_BINDING"),
    (
        "incompatible-schema",
        lambda x: x["graph"]["nodes"][1]["inputs"][0].update(schema={"type": "boolean"}),
        "DATAFLOW_SCHEMA",
    ),
    (
        "duplicate-input",
        lambda x: x["graph"]["nodes"][0]["inputs"].append(
            copy.deepcopy(x["graph"]["nodes"][0]["inputs"][0])
        ),
        "DATAFLOW_BINDING",
    ),
    (
        "duplicate-output",
        lambda x: x["graph"]["nodes"][0]["outputs"].append(
            copy.deepcopy(x["graph"]["nodes"][0]["outputs"][0])
        ),
        "DATAFLOW_BINDING",
    ),
    (
        "criterion-drift",
        lambda x: x["graph"]["nodes"][1]["bindings"].update(
            criterion=constant({"id": "other", "description": "other"})
        ),
        "SEMANTIC_BINDING",
    ),
    (
        "guard-source",
        lambda x: x["graph"]["edges"][0].update(
            guard={"source": upstream("absent", "x"), "pointer": "", "value": 0}
        ),
        "DATAFLOW_BINDING",
    ),
    (
        "external-judgment-schema",
        lambda x: x.update(judgment_schema={"$ref": "https://example.invalid/judgment"}),
        "SCHEMA_UNSUPPORTED",
    ),
    (
        "bad-config",
        lambda x: x["graph"]["nodes"][0].update(config_schema={"type": "null"}),
        "DATAFLOW_CONFIG",
    ),
]:
    bad = copy.deepcopy(d)
    change(bad)
    case("typed-" + name, "verification-definition", bad, code)
bad = copy.deepcopy(d)
bad["graph"]["nodes"][0]["operation"]["capability_id"] = "ConcreteProvider"
case("typed-malformed-capability", "verification-definition", bad, "PROTOCOL_STRUCTURE", "schema")
for name, change in [
    ("changed-producer", lambda r: r["nodes"][0]["information"].update(x=1)),
    ("changed-run-input", lambda r: r["run_inputs"].update(x=1)),
    ("unbound-snapshot", lambda r: r["nodes"][1]["input_values"].update(secret=42)),
    ("runtime-output-invalid", lambda r: r["nodes"][0]["observation"]["outputs"].update(x=False)),
    ("consumer-snapshot", lambda r: r["nodes"][1]["input_values"].update(x=1)),
]:
    bad = copy.deepcopy(run)
    change(bad)
    case("typed-" + name, "run-record", bad, "PROVENANCE_LINEAGE")
# Explicit failure is a valid observation. Its required information consumer is skipped.
failed = run_record(
    d,
    {"x": 0},
    {
        **obs,
        "derive": {
            "outputs": {},
            "error": {"code": "com.example.unavailable", "message": "No observation"},
            "usage": {"API_calls": {"unit": "call", "kind": "EXACT", "value": 1}},
        },
    },
)
case("typed-producer-error-blocks", "run-record", failed)
bad = copy.deepcopy(failed)
bad["nodes"][1] = copy.deepcopy(run["nodes"][1])
case("typed-stale-value-consumed", "run-record", bad, "PROVENANCE_LINEAGE")
# An ambient name is never a portable source.
failed["initial_context"] = {"x": 100}
case("typed-stale-ambient-ignored", "run-record", failed)
for reducer in [
    "ALL",
    "ANY",
    "MAJORITY",
    "MIN_SCORE",
    "MAX_SCORE",
    "AVERAGE",
    "WEIGHTED_AVERAGE",
    "WORST_SEVERITY",
]:
    c = {"reducer": reducer, "handling": HANDLING}
    if reducer == "WEIGHTED_AVERAGE":
        c["weights"] = {"check": 1}
    if reducer == "WORST_SEVERITY":
        c["severity_domain"] = {"id": "custom-v1", "levels": [{"label": "mild", "rank": 1}]}
    member = {**PASS, "score": 0.75, "severity": {"domain": "custom-v1", "label": "mild"}}
    aggregate_result = copy.deepcopy(PASS)
    if reducer in ("MIN_SCORE", "MAX_SCORE", "AVERAGE", "WEIGHTED_AVERAGE"):
        aggregate_result.pop("verdict")
        aggregate_result["score"] = 0.75
    if reducer == "WORST_SEVERITY":
        aggregate_result.pop("verdict")
        aggregate_result["severity"] = {"domain": "custom-v1", "label": "mild"}
    agg = node(
        "aggregate",
        "AGGREGATE",
        "openverify.aggregate",
        inputs=[port("check", {"type": "object"})],
        bindings={"check": upstream("judge")},
        config=c,
        members=["check"],
    )
    ad = definition(
        [node("derive", "DERIVE"), node("judge", "EVALUATE"), agg],
        [edge("derive", "aggregate"), edge("judge", "aggregate")],
    )
    ar = run_record(
        ad,
        {},
        {
            "derive": {"outputs": {}},
            "judge": {"outputs": {"result": member}},
            "aggregate": {"outputs": {"result": aggregate_result}},
        },
    )
    case("typed-aggregate-" + reducer.lower(), "run-record", ar)
    if reducer == "WEIGHTED_AVERAGE":
        bad = copy.deepcopy(ad)
        bad["graph"]["nodes"][-1]["config"]["weights"] = {"wrong": 1}
        case("typed-weight-identity-mismatch", "verification-definition", bad, "AGGREGATE_CONFIG")
    if reducer == "ALL":
        bad = copy.deepcopy(ad)
        bad["graph"]["nodes"][-1]["aggregate_inputs"] = ["wrong"]
        case(
            "typed-aggregate-membership-mismatch",
            "verification-definition",
            bad,
            "AGGREGATE_CONFIG",
        )
# Keep portable admission/timestamp regressions against the new explicit record shape.
case("complete-run-record", "run-record", run)
skip = run_record(d, {"x": 0}, {}, disabled=[n["id"] for n in d["graph"]["nodes"]])
skip["admission"] = {"outcome": "SKIP", "reason": "PROBABILITY p=0"}
skip["policy_evaluations"][-1]["outcome"] = copy.deepcopy(skip["admission"])
skip["definition"]["execution_policy"]["admission"] = {"strategy": "PROBABILITY", "probability": 0}
case("admission-skip-run", "run-record", skip)
for disposition in ("DEFERRED", "CANCELLED"):
    bad = copy.deepcopy(skip)
    bad["nodes"][1]["result"]["disposition"] = disposition
    case("admission-skip-" + disposition.lower() + "-node", "run-record", bad, "PROVENANCE_LINEAGE")
bad = copy.deepcopy(skip)
bad["final_results"]["judge"]["disposition"] = "DEFERRED"
case("admission-skip-final-mismatch", "run-record", bad, "PROVENANCE_LINEAGE")
for name, text, code in [
    ("utc-offset-run-record", "2026-01-01T00:00:00+00:00", None),
    ("utc-fractional-run-record", "2026-01-01T00:00:00.1234567+00:00", None),
    ("utc-lowercase-run-record", "2026-01-01t00:00:00z", None),
    ("non-utc-positive-run-record", "2026-01-01T00:00:00+01:00", "PROTOCOL_STRUCTURE"),
    ("non-utc-negative-run-record", "2026-01-01T00:00:00-05:00", "PROTOCOL_STRUCTURE"),
    ("timezone-missing-run-record", "2026-01-01T00:00:00", "PROTOCOL_STRUCTURE"),
    ("malformed-timestamp-run-record", "2026-13-01T00:00:00Z", "PROTOCOL_STRUCTURE"),
]:
    bad = copy.deepcopy(run)
    for item in [bad, *bad["nodes"]]:
        item["started_at"] = item["finished_at"] = text
    case(name, "run-record", bad, code, "schema")
# Retain earlier JSON type/lineage regressions under the typed record format.
bad = copy.deepcopy(run)
bad["nodes"][2]["upstream_results"] = {}
case("invalid-upstream-lineage", "run-record", bad, "PROVENANCE_LINEAGE")
subject_definition = copy.deepcopy(d)
subject_definition["subject"]["locator"] = 1
for n in subject_definition["graph"]["nodes"]:
    if n["kind"] in ("EVALUATE", "AGGREGATE"):
        n["bindings"]["subject"] = constant(subject_definition["subject"])
bad = run_record(subject_definition, {"x": 0}, obs)
bad["subject"]["locator"] = True
case("subject-number-boolean-mismatch", "run-record", bad, "PROVENANCE_LINEAGE")
number_observations = copy.deepcopy(obs)
number_observations["judge"]["outputs"]["result"]["output"] = {"v": 1}
bad = run_record(d, {"x": 0}, number_observations)
bad["nodes"][2]["upstream_results"]["judge"] = copy.deepcopy(
    bad["nodes"][2]["upstream_results"]["judge"]
)
bad["nodes"][2]["upstream_results"]["judge"]["output"]["v"] = True
case("upstream-number-boolean-mismatch", "run-record", bad, "PROVENANCE_LINEAGE")
bad = run_record(d, {"x": 0}, number_observations)
bad["final_results"] = copy.deepcopy(bad["final_results"])
bad["final_results"]["judge"]["output"]["v"] = True
case("final-number-boolean-mismatch", "run-record", bad, "PROVENANCE_LINEAGE")
bad = copy.deepcopy(run)
bad["nodes"][0]["information"]["x"] = 1
bad["nodes"][0]["observation"]["outputs"]["x"] = 1
case(
    "typed-changed-producer-consistent-output-old-consumer", "run-record", bad, "PROVENANCE_LINEAGE"
)
bad = copy.deepcopy(run)
bad["run_inputs"]["undeclared"] = 1
case("typed-undeclared-occurrence-input", "run-record", bad, "PROVENANCE_LINEAGE")
case(
    "typed-resolution-missing-value",
    "input-resolution",
    {"source": constant(None), "status": "AVAILABLE", "used_default": False},
    "DATAFLOW_BINDING",
)
case(
    "typed-resolution-unavailable-value",
    "input-resolution",
    {"source": constant(0), "status": "INVALID", "used_default": False, "value": 0},
    "DATAFLOW_BINDING",
)
case(
    "typed-guard-run-input",
    "verification-definition",
    {
        **copy.deepcopy(d),
        "graph": {
            **copy.deepcopy(d["graph"]),
            "edges": [
                {
                    **d["graph"]["edges"][0],
                    "guard": {
                        "source": {"kind": "RUN_INPUT", "name": "x"},
                        "pointer": "",
                        "value": 0,
                    },
                },
                *d["graph"]["edges"][1:],
            ],
        },
    },
)
# Usage/evidence are portable observations even on a failed Derive.
case(
    "typed-error-observation-with-usage",
    "execution-observation",
    {
        "outputs": {},
        "usage": {"API_calls": {"unit": "call", "kind": "EXACT", "value": 1}},
        "evidence": [{"message": "Attempted observation"}],
        "error": {"code": "com.example.unavailable", "message": "No observation"},
    },
)
# Custom reducers receive the same bound membership input as standard reducers.
custom = copy.deepcopy(ar)
custom_node = custom["definition"]["graph"]["nodes"][-1]
custom_node["operation"] = {
    "capability_id": "com.example.custom.aggregate",
    "capability_version": "1",
}
custom_node["config"] = {}
custom["nodes"][-1]["operation"] = custom_node["operation"]
case("typed-custom-aggregate", "run-record", custom)
bad = copy.deepcopy(d)
bad["graph"]["nodes"][0]["operation"]["capability_version"] = ""
case(
    "typed-malformed-capability-version",
    "verification-definition",
    bad,
    "PROTOCOL_STRUCTURE",
    "schema",
)
# A source failure cannot acquire a name-matching initial run value.
case("typed-run-source", "value-source", {"kind": "RUN_INPUT", "name": "x"})
case("typed-external-source", "value-source", {"kind": "EXTERNAL_REFERENCE", "reference": ref})
case("typed-upstream-source", "value-source", upstream("derive", "x"))
# Rejected Evidence meaning must not erase valid reported resource usage.
evidence_observation = {
    "outputs": {"x": 0},
    "usage": {"API_calls": {"unit": "call", "kind": "EXACT", "value": 1}},
    "evidence": [{}],
}
evidence_failed = run_record(
    d,
    {"x": 0},
    {
        **obs,
        "derive": {
            "outputs": {},
            "usage": evidence_observation["usage"],
            "error": {"code": "EVIDENCE_EMPTY", "message": "Evidence needs a meaningful component"},
        },
    },
)
evidence_failed["nodes"][0]["observation"] = copy.deepcopy(evidence_observation)
for n in evidence_failed["nodes"]:
    if n["node_id"] in ("judge", "other"):
        n["input_resolutions"]["x"]["status"] = "INVALID"
case("typed-rejected-evidence-retains-usage", "run-record", evidence_failed)
bad = copy.deepcopy(run)
bad["nodes"][0]["observation"] = copy.deepcopy(evidence_observation)
case("typed-invalid-evidence-accepted", "run-record", bad, "PROVENANCE_LINEAGE")
write(DIRECTORY / "manifest.json", manifest)
# Remove only obsolete, unlisted fixture files within the conformance directory.
listed = {c["input"] for c in cases} | {c["expected"] for c in cases}
for folder in ("valid", "invalid", "expected"):
    for path in (DIRECTORY / folder).glob("*.json"):
        if path.relative_to(DIRECTORY).as_posix() not in listed:
            path.unlink()
