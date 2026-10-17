"""Link schema enum declarations to concrete classified stimuli, without SUT imports."""
import json


def roots(case, kind):
    p, op = case.get("input", {}), case.get("operation")
    if op == "parse_result" and kind == "result":
        yield p
    if op in ("parse_object", "provider_object") and p.get("object_type") == kind:
        yield p["value"]
    if op == "provider_object" and p.get("object_type") == "outcome" and kind == "provider-error":
        if p["value"].get("error"):
            yield p["value"]["error"]
    if op == "parse_definition":
        if kind == "graph":
            yield p["graph"]
        if kind == "input-port":
            yield from p.get("run_inputs", [])
            for n in p["graph"]["nodes"]:
                yield from n.get("inputs", [])
        if kind == "output-port":
            for n in p["graph"]["nodes"]:
                yield from n.get("outputs", [])
    if op == "provider_trace":
        for step in p["steps"]:
            field = {"provider-event": "event", "outcome": "outcome", "invocation": "invocation",
                     "cancel-request": "request"}.get(kind)
            if field and field in step:
                yield step[field]
            if kind == "provider-error" and step.get("outcome", {}).get("error"):
                yield step["outcome"]["error"]
    if op == "availability" and case["expected"].get("applicable"):
        if kind == "input-resolution":
            yield {"status": p["status"]}
        if kind == "input-port":
            yield {"on_unavailable": p["handling"]}


def values(root, pointer):
    tokens = pointer.split("/")[1:]
    steps = []
    i = 0
    while i < len(tokens):
        if tokens[i] == "properties":
            steps.append(tokens[i + 1].replace("~1", "/").replace("~0", "~"))
            i += 2
        elif tokens[i] == "items":
            steps.append("*")
            i += 1
        elif tokens[i] in ("anyOf", "oneOf", "allOf"):
            i += 2
        else:
            i += 1
    pending = [root]
    for key in steps:
        pending = [child for item in pending for child in
                   (item if key == "*" and isinstance(item, list) else
                    [item[key]] if isinstance(item, dict) and key in item else [])]
    return pending


def coverage_rows(enums, cases, scenarios, master):
    runtime = []
    kinds = {n["id"]: n["kind"] for n in master["graph"]["nodes"]}
    for c in scenarios:
        if c["scenario"].get("nodes"):
            runtime.append({"id": c["id"], "operation": "parse_object", "input": {
                "object_type": "run-record", "value": {"nodes": [
                    {"kind": kinds[k], "state": v["state"]} for k, v in c["scenario"]["nodes"].items()]}}})
            runtime.append({"id": c["id"], "operation": "parse_object", "input": {
                "object_type": "policy-evaluation", "value": {"role": "ACTIVATION"}}})
            runtime.extend({"id": c["id"], "operation": "parse_object", "input": {
                "object_type": "policy-evaluation", "value": {"role": role}}} for role in ("SELECTION", "ADMISSION"))
    runtime += [{"id": "master.running_cancellation", "operation": "parse_object", "input": {
        "object_type": "run-record", "value": {"nodes": [{"kind": "DERIVE", "state": "CANCELLED"}]}}},
        {"id": "master.running_cancellation", "operation": "parse_object", "input": {
        "object_type": "cancellation-event", "value": {"phase": "RUNNING"}}},
        {"id": "master.cancellation_isolation", "operation": "parse_object", "input": {
        "object_type": "cancellation-event", "value": {"phase": "BEFORE_START"}}}]
    for number, enum in enumerate(enums):
        kind = enum["source"].split("/")[-1].removesuffix(".schema.json")
        witnesses = {}
        suite = "STRUCTURE"
        for pool, pool_suite in ((cases, "STRUCTURE"), (runtime, "MASTER EXECUTION")):
            found = {}
            for c in pool:
                for root in roots(c, kind):
                    for v in values(root, enum["pointer"]):
                        if v in enum["all_declared_states"]:
                            found.setdefault(json.dumps(v, sort_keys=True), c["id"])
            if len(found) > len(witnesses):
                witnesses, suite = found, pool_suite
        missing = [v for v in enum["all_declared_states"] if json.dumps(v, sort_keys=True) not in witnesses]
        yield {"requirement_id": f"enum.{number:02}.{kind}", "normative_section": [enum["source"] + "#" + enum["pointer"]],
            "finite_domain_or_interface_law": "Every declared enum value is explicitly classified",
            "all_declared_states": enum["all_declared_states"], "all_declared_transitions": None,
            "transition_scope": "Not applicable: value-domain classification",
            "scenario_ids": sorted(set(witnesses.values())), "suite": suite,
            "independently_frozen_expectation": witnesses, "missing_states": missing,
            "mutation_witness": "Remove/rename a declared enum value, or accept an invalid sentinel",
            "status": "uncovered" if missing else "covered", "verification": "UNVERIFIED; tests not run"}
