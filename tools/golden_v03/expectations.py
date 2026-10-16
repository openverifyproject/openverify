"""Specification-only master stimuli and expectations. Never imports the SUT.

Authority: spec/draft/{dataflow,aggregation,result,lifecycle,execution-policy}.md.
Earlier independent builders/oracles are reused without invoking their runners.
"""
from copy import deepcopy
from functools import lru_cache
import json

from tools.golden_v02.build_baseline import (
    SUBJECT, CRITERION, EXTERNAL, constant, definition, edge, node, port, upstream,
    success, nonexecution,
)
from tools.golden_v02.oracle import EXCEPTIONAL, REDUCERS, result, reduce_results

DOMAIN = {"id": "golden.severity", "levels": [
    {"label": "low", "rank": 1}, {"label": "high", "rank": 2}]}
USAGE = {"com.example.calls": {"kind": "EXACT", "unit": "call", "value": 2}}
POLICIES = {
    "ACTIVATION": {"outcome": "ACTIVATE", "reason": "scripted"},
    "SELECTION": {"subjects": [SUBJECT], "reason": "scripted"},
    "ADMISSION": {"outcome": "RUN", "reason": "scripted"},
}


@lru_cache(maxsize=1)
def master_json():
    """Immutable canonical wire definition, authored once, never a mutable graph."""
    d1 = node("D1", inputs=[port("run", {"type": "integer"}), port("constant"),
                            port("external")], bindings={
        "run": {"kind": "RUN_INPUT", "name": "payload"}, "constant": constant(3),
        "external": {"kind": "EXTERNAL_REFERENCE", "reference": EXTERNAL}},
        outputs=[{"name": "value", "schema": {"type": "integer"}, "role": "INFORMATION"}])
    d2 = node("D2", inputs=[port("optional", {"type": "integer"}, False, 7),
                            port("omitted", {"type": "integer"}, False)], bindings={
        "optional": {"kind": "RUN_INPUT", "name": "optional"},
        "omitted": {"kind": "RUN_INPUT", "name": "omitted"}})
    e1 = node("E1", "EVALUATE", [port("shared")],
              {"shared": {"kind": "RUN_INPUT", "name": "payload"}})
    e2 = node("E2", "EVALUATE", [port("data"), port("other"),
              port("defaulted", True, False, 11), port("omitted", True, False)], {
        "data": upstream("D1"), "other": upstream("D2"),
        "defaulted": upstream("D1"), "omitted": upstream("D1")})
    e3 = node("E3", "EVALUATE")
    c = node("C", "CONTROL", [port("checked")], {"checked": upstream("E3", "result")})
    left, right = node("left"), node("right")
    nodes = [d1, d2, e1, e2, e3, c, left, right]
    edges = [edge("D1", "E2"), edge("D2", "E2"), edge("E2", "E3"),
             edge("E1", "C"), edge("E3", "C"), edge("C", "left", {
                 "source": {"kind": "RUN_INPUT", "name": "guard"}, "pointer": "", "value": True}),
             edge("C", "right")]
    for name in (*REDUCERS, "CUSTOM"):
        members = ["a", "b", "c"]
        config = {"reducer": name, "handling": dict.fromkeys(EXCEPTIONAL, "IGNORE")}
        if name == "WEIGHTED_AVERAGE":
            config["weights"] = {"a": 1, "b": 2, "c": 3}
        if name == "WORST_SEVERITY":
            config["severity_domain"] = DOMAIN
        agg = node("A_" + name, "AGGREGATE", [*(port(x) for x in members), port("members")], {
            "a": upstream("E1", "result"), "b": upstream("E2", "result"),
            "c": upstream("E3", "result"), "members": constant(members)},
            config={} if name == "CUSTOM" else config,
            capability="com.example.golden.custom_aggregate" if name == "CUSTOM" else "openverify.aggregate")
        agg["aggregate_inputs"] = members
        nodes.append(agg)
        edges.extend(edge(src, agg["id"]) for src in ("E1", "E2", "E3", "left", "right"))
    d = definition(nodes, edges, [port("payload", {"type": "integer"}),
        port("optional", {"type": "integer"}, False), port("omitted", {"type": "integer"}, False),
        port("guard", {"type": "boolean"}, False, True),
        *(port(role.lower(), True, False, POLICIES[role]) for role in POLICIES)])
    d["id"], d["version"] = "golden.v03.master", "0.3.0"
    for role in POLICIES:
        d["execution_policy"][role.lower()] = {
            "operation": {"capability_id": "com.example.golden.policy_" + role.lower(),
                          "capability_version": "1"},
            "inputs": [port("choice")], "bindings": {
                "choice": {"kind": "RUN_INPUT", "name": role.lower()}}, "config": {}}
    return json.dumps(d, sort_keys=True, separators=(",", ":"))


def base_scenario():
    d = json.loads(master_json())
    behaviors = {"D1": {"outputs": {"value": 5}}, "D2": {"outputs": {"value": 7}},
                 "C": {"outputs": {"decision": {"protocol": "draft", "kind": "CONTINUE"}}},
                 "left": {"outputs": {"value": "left"}}, "right": {"outputs": {"value": "right"}},
                 "A_CUSTOM": {"outputs": {"result": result("PASS", output={"custom": True})}}}
    for index, name in enumerate(("E1", "E2", "E3")):
        behaviors[name] = {"outputs": {"result": result("PASS", score=index / 2,
            severity={"domain": DOMAIN["id"], "label": "high" if index == 2 else "low"},
            evidence=[{"message": name}])}}
    return {"definition": d, "inputs": {"payload": 5}, "behaviors": behaviors,
            "policies": deepcopy(POLICIES), "nodes": {}}


def freeze_scenario(s, disabled=None, errors=None):
    """Finite hand-authored effects + mathematical reducers, never graph simulation."""
    disabled, errors = disabled or {}, errors or {}
    by_id = {n["id"]: n for n in s["definition"]["graph"]["nodes"]}
    for identity, b in s["behaviors"].items():
        if identity in disabled:
            facts = nonexecution(disabled[identity])
        elif identity in errors:
            facts = {"state": "ERROR", "information": {}, "result": result("ERROR")}
            if errors[identity] is not None:
                facts["reason"] = errors[identity]
        else:
            facts = success(by_id[identity], b["outputs"])
            if facts.get("result", {}).get("execution_outcome") == "ERROR":
                facts["state"] = "ERROR"
        s["nodes"][identity] = facts
    members = [s["nodes"][n]["result"] for n in ("E1", "E2", "E3")]
    for name in REDUCERS:
        identity = "A_" + name
        if identity in disabled:
            s["nodes"][identity] = nonexecution(disabled[identity])
            continue
        config = deepcopy(by_id[identity]["config"])
        if name == "WEIGHTED_AVERAGE":
            config["weights"] = [1, 2, 3]
        answer = reduce_results(name, members, config)
        s["nodes"][identity] = (
            {"state": "ERROR", "reason": "openverify.computation_error", "information": {},
             "result": result("ERROR")} if "error_code" in answer
            else {"state": "SUCCESS", "information": {}, "result": answer["result"]})
    return s


def master_scenarios():
    """Each yield is a distinct observable effect, never a value-only graph copy."""
    def emit(identity, s, **kwargs):
        return {"id": "master." + identity, "category": identity.split(".")[0],
                "scenario": freeze_scenario(s, **kwargs)}
    yield emit("normal", base_scenario())
    for label in ("FAIL", "UNKNOWN", "NOT_APPLICABLE", "ERROR", "KNOWN"):
        s = base_scenario()
        s["behaviors"]["E2"]["outputs"]["result"] = result(label)
        yield emit("result." + label, s)
    for identity, reason, change in (
        ("wrong_type", "OUTPUT_INVALID", {"outputs": {"value": "wrong"}}),
        ("missing", "OUTPUT_MISSING", {"outputs": {}}),
        ("extra", None, {"outputs": {"value": 5, "extra": 1}}),
        ("provider_error", "com.example.scripted_failure", {"error": {
            "code": "com.example.scripted_failure", "message": "scripted"}}),
        ("exception", "TRANSPORT_ERROR", {"raise": True}),
        ("duplicate_terminal", "PROTOCOL_VIOLATION", {"duplicate_terminal": True}),
        ("invalid_event", "PROTOCOL_VIOLATION", {"invalid_event": True}),
    ):
        s = base_scenario()
        s["behaviors"]["D1"].update(change)
        yield emit("fault." + identity, s, errors={"D1": reason}, disabled={"E2": "INPUT_UNAVAILABLE"})
    for label, value in (("malformed", {"protocol": "draft", "disposition": "EXECUTED"}),
                         ("SKIP", result("SKIP")), ("DEFERRED", result("DEFERRED")),
                         ("CANCELLED", result("CANCELLED"))):
        s = base_scenario()
        s["behaviors"]["E1"]["outputs"]["result"] = value
        yield emit("invalid_result." + label, s, errors={"E1": "RESULT_STATE" if label == "malformed" else "OUTPUT_INVALID"})
    s = base_scenario()
    s["behaviors"]["C"]["outputs"]["decision"] = {"protocol": "draft", "kind": "ROUTE"}
    yield emit("invalid_decision", s, errors={"C": None})
    for kind in ("STOP_SUCCESS", "STOP_FAILURE", "RETRY", "DEFER", "ROUTE"):
        s = base_scenario()
        s["behaviors"]["C"]["outputs"]["decision"]["kind"] = kind
        disabled = {}
        if kind == "ROUTE":
            s["behaviors"]["C"]["outputs"]["decision"]["destination"] = "left"
            disabled = {"right": "ROUTE_EXCLUDED"}
        else:
            reason = {"RETRY": "RETRY_REQUESTED", "DEFER": "CONTROL_DEFER"}.get(kind, "CONTROL_STOP")
            disabled = {n["id"]: reason for n in s["definition"]["graph"]["nodes"][6:]}
        yield emit("control." + kind, s, disabled=disabled)
    s = base_scenario()
    s["inputs"]["guard"] = False
    yield emit("guard.false", s, disabled={"left": "GUARD_FALSE"})
    s = base_scenario()
    s["inputs"].update(optional=13, omitted=17)
    yield emit("inputs.supplied", s)
    for kind in ("SKIP", "DEFER"):
        s = base_scenario()
        s["policies"]["ADMISSION"]["outcome"] = kind
        s["inputs"]["admission"] = s["policies"]["ADMISSION"]
        yield emit("admission." + kind, s, disabled={
            n["id"]: "ADMISSION_" + kind for n in s["definition"]["graph"]["nodes"]})
    for name, role, outcome, error in (
        ("inactive", "ACTIVATION", {"outcome": "DO_NOT_ACTIVATE", "reason": "scripted"}, "NO_OCCURRENCE"),
        ("unselected", "SELECTION", {"subjects": [], "reason": "scripted"}, "NO_OCCURRENCE"),
        *(("invalid_" + r.lower(), r, {}, "POLICY_OUTPUT") for r in POLICIES),
    ):
        s = base_scenario()
        s["policies"][role] = outcome
        s["inputs"][role.lower()] = outcome
        yield {"id": "master.policy." + name, "category": "policy", "scenario": s,
               "error_code": error}
    for name, inputs in (("missing", {}), ("invalid", {"payload": "wrong"}),
                         ("undeclared", {"payload": 5, "unknown": 0})):
        s = base_scenario()
        s["inputs"] = inputs
        yield {"id": "master.inputs." + name, "category": "inputs", "scenario": s,
               "error_code": "RUN_INPUT"}
    s = base_scenario()
    s["behaviors"]["D1"].update(usage=USAGE, events=[
        {"kind": "resource_usage", "payload": {"com.example.calls": {
            "kind": "EXACT", "unit": "call", "value": 1}}},
        {"kind": "evidence", "payload": {"message": "observed evidence"}}])
    yield emit("usage.final_authoritative", s)
    yield emit("concurrency.barriers", base_scenario())
    yield emit("provenance.anchors", base_scenario())
