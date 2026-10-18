"""Small specification-derived tables, not a runtime or replacement Relay.

Authority: spec/draft/{result,aggregation,lifecycle,execution-policy,dataflow}.md.
Schemas are read offline as normative artifacts. Never imports openverify.
"""
from __future__ import annotations

import itertools
import json
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from tools.golden.compare import equal, same

ROOT = Path(__file__).resolve().parents[2]
MISSING = object()
EXCEPTIONAL = ("UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING")
REDUCERS = ("ALL", "ANY", "MAJORITY", "MIN_SCORE", "MAX_SCORE", "AVERAGE", "WEIGHTED_AVERAGE", "WORST_SEVERITY")
KINDS = ("DERIVE", "EVALUATE", "AGGREGATE", "CONTROL")
DECISIONS = ("CONTINUE", "ROUTE", "STOP_SUCCESS", "STOP_FAILURE", "RETRY", "DEFER")
LIFECYCLE = {
    "ADMISSION_SKIP": ("SKIPPED", "NONEXECUTED"),
    "ADMISSION_DEFER": ("DEFERRED", "NONEXECUTED"),
    "CONTROL_STOP": ("SKIPPED", "NONEXECUTED"),
    "CONTROL_DEFER": ("DEFERRED", "NONEXECUTED"),
    "RETRY_REQUESTED": ("SKIPPED", "NONEXECUTED"),
    "ROUTE_EXCLUDED": ("SKIPPED", "NONEXECUTED"),
    "GUARD_FALSE": ("SKIPPED", "NONEXECUTED"),
    "INPUT_UNAVAILABLE": ("SKIPPED", "NONEXECUTED"),
    "CANCELLATION": ("CANCELLED", "NONEXECUTED"),
}
RESULT_CONTROL_NULLS = ("execution_outcome", "applicability", "determination", "verdict", "score", "severity")


def strict_loads(raw: str | bytes):
    def pairs(items):
        d = {}
        for key, value in items:
            if key in d:
                raise ValueError(f"duplicate JSON key: {key}")
            d[key] = value
        return d
    def bad(value):
        raise ValueError(f"nonfinite number: {value}")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


@lru_cache(maxsize=1)
def schema_registry():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    schemas = []
    for folder in (ROOT / "schemas/draft", ROOT / "provider-contract/schemas/draft"):
        for path in folder.glob("*.json"):
            obj = strict_loads(path.read_bytes())
            schemas.append((obj["$id"], Resource.from_contents(obj)))
    return Registry().with_resources(schemas)


def schema_errors(name: str, data, provider: bool = False) -> list:
    from jsonschema import Draft202012Validator
    registry = schema_registry()
    prefix = "urn:openverify:provider:0.1:" if provider else "urn:verification:draft:"
    return list(Draft202012Validator({"$ref": prefix + name}, registry=registry).iter_errors(data))


def normalized_result(r: dict) -> dict:
    d = deepcopy(r)
    for key in RESULT_CONTROL_NULLS:
        if d.get(key, MISSING) is None:
            d.pop(key)
    for key, default in (("evidence", []), ("usage", {}), ("metadata", {}), ("extensions", [])):
        d.setdefault(key, deepcopy(default))
    return d


def result_error(r: dict) -> str | None:
    if r.get("protocol") != "draft":
        return "PROTOCOL_VERSION"
    if schema_errors("result", r):
        return "PROTOCOL_STRUCTURE"
    d = normalized_result(r)
    evaluation = ("applicability", "determination", "judgment", "verdict", "score", "severity")
    if d["disposition"] != "EXECUTED":
        invalid = any(k in d for k in ("execution_outcome", *evaluation))
    elif d.get("execution_outcome") == "ERROR":
        invalid = any(k in d for k in evaluation)
    elif d.get("execution_outcome") != "SUCCESS":
        invalid = True
    elif d.get("applicability") == "NOT_APPLICABLE":
        invalid = any(k in d for k in evaluation[1:])
    elif d.get("applicability") != "APPLICABLE":
        invalid = True
    elif d.get("determination") == "UNKNOWN":
        invalid = any(k in d for k in evaluation[2:])
    else:
        invalid = d.get("determination") != "KNOWN"
    if invalid:
        return "RESULT_STATE"
    for evidence in d["evidence"]:
        if not any(evidence.get(k) is not None for k in ("message", "artifact_ref", "locator", "structured_data")):
            return "EVIDENCE_EMPTY"
    if any(ext["required"] for ext in d["extensions"]):
        return "EXTENSION_UNSUPPORTED"
    return None


def projection(r: dict) -> str | None:
    if result_error(r):
        raise ValueError("cannot project invalid Result")
    r = normalized_result(r)
    if r["disposition"] == "SKIPPED":
        return "SKIP"
    if r["disposition"] != "EXECUTED":
        return None
    if r["execution_outcome"] == "ERROR":
        return "ERROR"
    if r["applicability"] != "APPLICABLE":
        return None
    if r["determination"] == "UNKNOWN":
        return "UNKNOWN"
    return r.get("verdict")


def result(label: str, **observations) -> dict:
    r = {"protocol": "draft", "disposition": "EXECUTED"}
    if label in ("SKIP", "DEFERRED", "CANCELLED"):
        r["disposition"] = "SKIPPED" if label == "SKIP" else label
    elif label == "ERROR":
        r["execution_outcome"] = "ERROR"
    else:
        r.update(execution_outcome="SUCCESS", applicability="APPLICABLE")
        if label == "NOT_APPLICABLE":
            r["applicability"] = label
        else:
            r["determination"] = "UNKNOWN" if label == "UNKNOWN" else "KNOWN"
            if label in ("PASS", "FAIL"):
                r["verdict"] = label
    r.update(observations)
    return r


def result_axes():
    axes = (
        ("disposition", ("EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED")),
        ("execution_outcome", (MISSING, None, "SUCCESS", "ERROR")),
        ("applicability", (MISSING, None, "APPLICABLE", "NOT_APPLICABLE")),
        ("determination", (MISSING, None, "KNOWN", "UNKNOWN")),
        ("verdict", (MISSING, None, "PASS", "FAIL")),
    )
    for values in itertools.product(*(v for _, v in axes)):
        yield {"protocol": "draft", **{k: v for (k, _), v in zip(axes, values) if v is not MISSING}}


def reduce_results(name: str, inputs: list[dict], config: dict) -> dict:
    """Mathematical reducer only, no graph execution or production dispatch.

    Numeric answers use exact rational arithmetic. Generated portable cases choose
    exactly representable answers; other precision cases are explicitly blocked.
    """
    handling = config.get("handling", {})
    if set(handling) != set(EXCEPTIONAL) or any(v not in ("REJECT", "IGNORE") for v in handling.values()):
        return {"error_code": "AGGREGATE_CONFIG"}
    weights = config.get("weights", [1] * len(inputs))
    if name == "WEIGHTED_AVERAGE":
        if len(weights) != len(inputs) or any(isinstance(w, bool) or not isinstance(w, (int, float)) or w < 0 for w in weights) or sum(weights) <= 0:
            return {"error_code": "AGGREGATE_CONFIG"}
    wanted = "verdict" if name in REDUCERS[:3] else "severity" if name == "WORST_SEVERITY" else "score"
    kept = []
    evidence = []
    for i, r in enumerate(inputs):
        label = projection(r)
        if r.get("applicability") == "NOT_APPLICABLE":
            label = "NOT_APPLICABLE"
        if r["disposition"] in ("DEFERRED", "CANCELLED"):
            label = r["disposition"]
        category = label if label in EXCEPTIONAL else "MISSING" if r.get(wanted) is None else None
        if category:
            if handling[category] == "REJECT":
                return {"error_code": "AGGREGATE_INPUT"}
            continue
        kept.append((i, r[wanted]))
        evidence.extend(r.get("evidence", []))
    if not kept:
        return {"error_code": "AGGREGATE_INPUT"}
    values = [v for _, v in kept]
    obs = {"evidence": evidence}
    if wanted == "verdict":
        passed = values.count("PASS")
        if name == "MAJORITY" and passed * 2 == len(values):
            return {"error_code": "AGGREGATE_INPUT"}
        verdict = all(v == "PASS" for v in values) if name == "ALL" else any(v == "PASS" for v in values) if name == "ANY" else passed * 2 > len(values)
        obs["verdict"] = "PASS" if verdict else "FAIL"
    elif wanted == "score":
        nums = [Fraction(v) for v in values]
        if name == "MIN_SCORE":
            score = min(nums)
        elif name == "MAX_SCORE":
            score = max(nums)
        elif name == "AVERAGE":
            score = sum(nums) / len(nums)
        else:
            retained = [Fraction(weights[i]) for i, _ in kept]
            if sum(retained) <= 0:
                return {"error_code": "AGGREGATE_INPUT"}
            score = sum(v * w for v, w in zip(nums, retained)) / sum(retained)
        obs["score"] = float(score)
    else:
        domain = config.get("severity_domain", {})
        levels = domain.get("levels", [])
        ranks = {x["label"]: x["rank"] for x in levels}
        if not levels or len(ranks) != len(levels) or len(set(ranks.values())) != len(levels):
            return {"error_code": "AGGREGATE_CONFIG"}
        if any(v["domain"] != domain["id"] or v["label"] not in ranks for v in values):
            return {"error_code": "AGGREGATE_INPUT"}
        obs["severity"] = max(values, key=lambda v: ranks[v["label"]])
    return {"result": result("KNOWN", **obs)}


def opportunity(activation: str, selected: bool, admission: str) -> dict:
    if activation == "DO_NOT_ACTIVATE" or not selected:
        return {"occurrence": False, "error_code": "NO_OCCURRENCE"}
    if admission == "RUN":
        return {"occurrence": True, "executes": True}
    return {"occurrence": True, "executes": False, "reason": "ADMISSION_" + admission}


def availability(producer: dict, output_role: str, published: bool, schema_valid: bool = True) -> str:
    """Single binding truth table; no ambient state or graph runner."""
    if output_role == "RESULT" and producer.get("result") is not None:
        return "AVAILABLE" if schema_valid else "INVALID"
    if producer["state"] in ("NONEXECUTED", "CANCELLED"):
        return "PRODUCER_NOT_EXECUTED"
    if producer["state"] == "ERROR":
        return "PRODUCER_ERROR"
    if not published:
        return "OUTPUT_MISSING"
    return "AVAILABLE" if schema_valid else "INVALID"


def check_record(record: dict, scenario: dict) -> None:
    """Reconstruct snapshots without a provider rerun. Expected node facts are frozen.

    Checks identity, typed bindings, dependencies, resource/timing separation and
    lifecycle; does not authenticate honest execution or reproduce local hashes.
    """
    from tools.golden.compare import Difference, fields, utc
    if schema_errors("run-record", record):
        raise Difference("RunRecord does not match normative wire schema")
    definition = scenario["definition"]
    # SDK serialization may materialize documented empty optional containers.
    equal(definition["id"], record["definition"]["id"], "/definition/id")
    equal(definition["version"], record["definition"]["version"], "/definition/version")
    equal(definition["subject"], record["subject"], "/subject")
    equal(scenario.get("inputs", {}), record["run_inputs"], "/run_inputs")
    nodes = {n["node_id"]: n for n in record["nodes"]}
    authored = {n["id"]: n for n in definition["graph"]["nodes"]}
    if len(nodes) != len(record["nodes"]) or nodes.keys() != authored.keys():
        raise Difference("node identity set/multiplicity differs")
    begin, end = utc(record["started_at"]), utc(record["finished_at"])
    if begin > end:
        raise Difference("run timing reversed")
    for edge in definition["graph"].get("edges", []):
        if utc(nodes[edge["from_node"]]["finished_at"]) > utc(nodes[edge["to_node"]]["started_at"]):
            raise Difference("dependency started before predecessor finished")
    bindings = record.get("provider_bindings", {})
    for identity, n in nodes.items():
        spec = authored[identity]
        equal(spec["operation"], n["operation"], f"/{identity}/operation")
        equal(spec["kind"], n["kind"], f"/{identity}/kind")
        if not begin <= utc(n["started_at"]) <= utc(n["finished_at"]) <= end:
            raise Difference(f"{identity}: timing outside run")
        expected = scenario["nodes"][identity]
        for key, val in expected.items():
            if key == "result":
                if n.get("result") is None:
                    raise Difference(f"{identity}: missing result")
                if val.get("execution_outcome") == "SUCCESS":
                    equal(normalized_result(val), normalized_result(n["result"]), f"/{identity}/result")
                else:
                    # Error diagnostics contain runtime messages; lifecycle reasons
                    # remain exact and evaluation fields are independently forbidden.
                    fields(val, n["result"], f"/{identity}/result")
                if result_error(n["result"]):
                    raise Difference(f"{identity}: invalid result axes")
            elif key == "absent":
                for absent in val:
                    if n.get(absent) not in (None, {}, []):
                        raise Difference(f"{identity}: forbidden {absent}")
            else:
                fields({key: val}, n, "/" + identity)
        ports = {p["name"]: p for p in spec["inputs"]}
        equal(sorted(ports), sorted(n["input_resolutions"]), f"/{identity}/resolution names")
        consumed = {}
        for name, port in ports.items():
            resolution = n["input_resolutions"][name]
            source = spec["bindings"].get(name)
            if source is not None:
                equal(source, resolution.get("source"), f"/{identity}/{name}/source")
            value = MISSING
            if source:
                kind = source["kind"]
                if kind == "CONSTANT":
                    value = source["value"]
                elif kind == "EXTERNAL_REFERENCE":
                    value = source["reference"]
                elif kind == "RUN_INPUT":
                    value = record["run_inputs"].get(source["name"], MISSING)
                    if value is MISSING:
                        declaration = next(p for p in definition["run_inputs"] if p["name"] == source["name"])
                        if declaration["on_unavailable"] == "DEFAULT":
                            value = declaration["default"]["value"]
                else:
                    producer = nodes[source["node_id"]]
                    declared = next(p for p in authored[source["node_id"]]["outputs"] if p["name"] == source["output"])
                    if declared["role"] == "RESULT":
                        value = producer.get("result", MISSING)
                    elif declared["role"] == "DECISION":
                        value = producer.get("decision", MISSING)
                    else:
                        value = producer["information"].get(source["output"], MISSING)
            if resolution["used_default"]:
                if port["on_unavailable"] != "DEFAULT":
                    raise Difference("undeclared default")
                value = port["default"]["value"]
            if "value" in resolution:
                if value is MISSING:
                    raise Difference("consumed value has no declared available source")
                # Result control defaults are serialization details, not a new source.
                if source and source["kind"] == "UPSTREAM_OUTPUT" and isinstance(value, dict) and value.get("protocol") == "draft" and "disposition" in value:
                    equal(normalized_result(value), normalized_result(resolution["value"]))
                else:
                    equal(value, resolution["value"], f"/{identity}/{name}/value")
                consumed[name] = resolution["value"]
            elif resolution["status"] == "AVAILABLE":
                raise Difference("AVAILABLE resolution without value")
        equal(consumed, n["input_values"], f"/{identity}/input_values")
        if n.get("provider_binding"):
            binding = n["provider_binding"]
            equal(binding, bindings.get(identity), f"/{identity}/provider_binding")
            fields(spec["operation"], binding)
            equal(binding["provider_id"], n["executor_ref"])
            equal(binding["provider_version"], n["executor_version"])
        if n["state"] == "NONEXECUTED":
            for forbidden in ("provider_binding", "executor_ref", "executor_version", "observation", "decision"):
                if n.get(forbidden) is not None:
                    raise Difference(f"nonexecution has {forbidden}")
            if n["information"] or identity in bindings:
                raise Difference("nonexecution published information/binding")
            if n.get("reason") not in LIFECYCLE:
                raise Difference("missing lifecycle cause")
            disposition, _ = LIFECYCLE[n["reason"]]
            equal(disposition, n["result"]["disposition"])
            equal(n["reason"], n["result"]["output"]["reason"])
        if n.get("result") is not None:
            equal(n["result"], record["final_results"].get(identity), f"/{identity}/final_result")
    for role, entry in zip(("ACTIVATION", "SELECTION", "ADMISSION"), record["policy_evaluations"]):
        equal(role, entry["role"])
    if len(record["policy_evaluations"]) != 3:
        raise Difference("missing policy history")
    equal(record["admission"], record["policy_evaluations"][2]["outcome"])
