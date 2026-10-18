"""Small reviewable oracles derived from normative prose, not implementation.

Result: spec/draft/result.md. Reducers: aggregation.md. Ports: dataflow.md.
Provider automaton: provider-contract/spec/draft/lifecycle.md.
All input values below are authored stimuli, never captured SUT outputs.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product

DISPOSITIONS = ("EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED")
AXES = {"execution_outcome": ("SUCCESS", "ERROR"), "applicability": ("APPLICABLE", "NOT_APPLICABLE"),
        "determination": ("KNOWN", "UNKNOWN"), "verdict": ("PASS", "FAIL")}
KINDS = ("DERIVE", "EVALUATE", "CONTROL", "AGGREGATE")
ROLES = ("INFORMATION", "RESULT", "DECISION")
SOURCES = ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE", "UPSTREAM_OUTPUT")
STATUSES = ("AVAILABLE", "ABSENT", "PRODUCER_NOT_EXECUTED", "PRODUCER_ERROR", "OUTPUT_MISSING", "INVALID")
HANDLERS = ("BLOCK", "OMIT", "DEFAULT")
EXCEPTIONS = ("UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING")
REDUCERS = ("ALL", "ANY", "MAJORITY", "MIN_SCORE", "MAX_SCORE", "AVERAGE", "WEIGHTED_AVERAGE", "WORST_SEVERITY")
TERMINALS = ("COMPLETED", "ERROR", "CANCELLED", "DEADLINE_EXCEEDED")
EVENTS = ("progress", "evidence", "artifact", "resource_usage", "diagnostic", "extension")
OBSERVATIONS = ("judgment", "score", "severity", "evidence", "output", "usage", "metadata", "extensions")
ARTIFACT = {"id": "v4:subject", "type": "application/json", "locator": {"authored": "subject"}}
CRITERION = {"id": "v4:criterion", "description": "Authored input is preserved"}
CAPABILITY = "com.example.golden.operation"
PROVIDER = "com.example.golden.provider"
SEVERITY = {"id": "v4:severity:1", "levels": [{"label": "low", "rank": 1}, {"label": "high", "rank": 9}]}


def constant(value):
    return {"kind": "CONSTANT", "value": value}


def port(name, schema=True, required=True, handler=None):
    v = {"name": name, "schema": schema, "required": required, "on_unavailable": handler or ("BLOCK" if required else "OMIT")}
    if v["on_unavailable"] == "DEFAULT":
        v["default"] = constant(None)
    return v


def definition(nodes=None, edges=None):
    return {"protocol": "draft", "id": "v4.authored", "version": "1", "subject": ARTIFACT,
            "criterion": CRITERION, "judgment_schema": True, "run_inputs": [],
            "graph": {"nodes": nodes or [], "edges": edges or []},
            "execution_policy": {"activation": {"executor_ref": "MANUAL"},
                                 "selection": {"executor_ref": "EXPLICIT"}, "admission": {"strategy": "ALWAYS"}}}


def node(name="n", kind="DERIVE"):
    n = {"id": name, "kind": kind, "operation": {"capability_id": CAPABILITY, "capability_version": "1"},
         "inputs": [], "outputs": [], "bindings": {}, "config": {}}
    if kind in {"EVALUATE", "AGGREGATE"}:
        for key, value in [("subject", ARTIFACT), ("criterion", CRITERION)]:
            n["inputs"].append(port(key)); n["bindings"][key] = constant(value)
        n["outputs"] = [{"name": "result", "schema": True, "role": "RESULT"}]
    if kind == "CONTROL":
        n["outputs"] = [{"name": "decision", "schema": True, "role": "DECISION"}]
    if kind == "AGGREGATE":
        n["inputs"].append(port("members")); n["bindings"]["members"] = constant([])
        n["aggregate_inputs"] = []
    return n


def known(**observations):
    return {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": "SUCCESS",
            "applicability": "APPLICABLE", "determination": "KNOWN", **observations}


def result_valid(r):
    """Nullable categorical controls collapse to bottom; judgments do not."""
    e, a, d, v = (r.get(k) for k in AXES)
    absent_eval = all(r.get(k) is None for k in ("applicability", "determination", "verdict", "score", "severity")) and "judgment" not in r
    if r["disposition"] != "EXECUTED":
        return e is None and absent_eval
    if e == "ERROR":
        return absent_eval
    if e != "SUCCESS" or a not in AXES["applicability"]:
        return False
    if a == "NOT_APPLICABLE":
        return d is None and v is None and r.get("score") is None and r.get("severity") is None and "judgment" not in r
    if d == "UNKNOWN":
        return v is None and r.get("score") is None and r.get("severity") is None and "judgment" not in r
    return d == "KNOWN" and v in (None, "PASS", "FAIL")


def semantic_results():
    for disp in DISPOSITIONS:
        for coords in product(*[(None, *v) for v in AXES.values()]):
            r = {"protocol": "draft", "disposition": disp, **{k:v for k,v in zip(AXES, coords) if v is not None}}
            if result_valid(r):
                yield r


def flatten(r):
    if r["disposition"] == "SKIPPED": return "SKIP"
    if r["disposition"] != "EXECUTED": return None
    if r["execution_outcome"] == "ERROR": return "ERROR"
    if r.get("applicability") != "APPLICABLE": return None
    if r["determination"] == "UNKNOWN": return "UNKNOWN"
    return r.get("verdict")


def resource_valid(kind, values):
    present = tuple(v is not None for v in values)
    return present == {"EXACT": (True,False,False), "ESTIMATED": (True,False,False),
                       "RANGE": (False,True,True), "UNKNOWN": (False,False,False)}[kind]


def acyclic(n, edges):
    """Independent transitive closure: diagonal reachability detects a cycle."""
    reach = [[False]*n for _ in range(n)]
    for a,b in edges: reach[a][b] = True
    for k in range(n):
        for i in range(n):
            for j in range(n): reach[i][j] |= reach[i][k] and reach[k][j]
    return not any(reach[i][i] for i in range(n))


def primitive_overlap(a,b):
    return a == b or {a,b} == {"integer", "number"}


def event_allowed(kind, stream, resource, vcp):
    return bool(stream and (kind not in {"evidence", "artifact", "resource_usage"} or vcp)
                and (kind != "resource_usage" or resource))


def terminal_allowed(state, cancelled, deadline):
    if deadline == "EXPIRED": return state == "DEADLINE_EXCEEDED"
    if state == "DEADLINE_EXCEEDED": return False
    return state != "CANCELLED" or bool(cancelled)


def exceptional(category):
    if category in {"SKIP", "DEFERRED", "CANCELLED"}:
        return {"protocol": "draft", "disposition": "SKIPPED" if category == "SKIP" else category}
    if category == "ERROR": return {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": "ERROR"}
    if category == "NOT_APPLICABLE": return {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": "SUCCESS", "applicability": "NOT_APPLICABLE"}
    if category == "UNKNOWN": return {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": "SUCCESS", "applicability": "APPLICABLE", "determination": "UNKNOWN"}
    return known()


def reduce_values(reducer, values, weights=None):
    """Mathematical operation on retained independent observations."""
    if not values: return {"error": "AGGREGATE_INPUT"}
    if reducer in {"ALL", "ANY", "MAJORITY"}:
        p = sum(v == "PASS" for v in values); f = len(values)-p
        if reducer == "MAJORITY" and p == f: return {"error": "AGGREGATE_INPUT"}
        passed = p == len(values) if reducer == "ALL" else (p > 0 if reducer == "ANY" else p > f)
        return {"verdict": "PASS" if passed else "FAIL"}
    if reducer == "WORST_SEVERITY": return {"severity": {"domain": SEVERITY["id"], "label": max(values, key=lambda v: {"low":1,"high":9}[v])}}
    if reducer == "MIN_SCORE": value = min(values)
    elif reducer == "MAX_SCORE": value = max(values)
    elif reducer == "AVERAGE": value = sum(map(Fraction,values))/len(values)
    else:
        if any(w < 0 for w in weights) or sum(weights) <= 0: return {"error": "AGGREGATE_INPUT"}
        value = sum(Fraction(v)*Fraction(w) for v,w in zip(values,weights))/sum(map(Fraction,weights))
    return {"score": float(value)}


def manifest(stream=True, resource=True, vcp=True, cancel=True, deadlines=True):
    cap = {"capability_id": CAPABILITY, "capability_version": "1", "input_schema": True,
           "config_schema": True, "output_schema": True,
           "lifecycle_features": {"streaming": stream, "cancellation": cancel, "deadlines": deadlines, "resource_reporting": resource}}
    if vcp: cap["vcp_version"] = "draft"
    return {"provider_id": PROVIDER, "provider_version": "1", "supported_contract_versions": ["0.1"],
            "supported_vcp_versions": ["draft"] if vcp else [], "capabilities": [cap]}


def invocation(vcp=True):
    v = {"invocation_id": "v4-attempt", "contract_version": "0.1", "capability_id": CAPABILITY,
         "capability_version": "1", "input": {}, "config": {}}
    if vcp: v["vcp_version"] = "draft"
    return v


def payload(kind):
    return {"progress": {"fraction":0.5}, "diagnostic": {"message":"authored"},
            "evidence": {"message":"authored evidence"}, "artifact": ARTIFACT,
            "resource_usage": {"tokens": {"unit":"token", "kind":"EXACT", "value":2}},
            "extension": {"namespace":"com.example.golden.event", "data":None}}[kind]
