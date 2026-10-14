"""Protocol-authored JSON helpers for fixtures/examples (no SDK implementation dependency)."""

from copy import deepcopy

SUBJECT = {"id": "article-1", "type": "text/plain", "locator": {"host_key": "text"}}
CRITERION = {"id": "readable-prose", "description": "Contains no banned phrase and is nonempty."}


def port(name, schema=None, required=True, default=None):
    p = {
        "name": name,
        "schema": {} if schema is None else schema,
        "required": required,
        "on_unavailable": "BLOCK" if required else "OMIT",
    }
    if default is not None:
        p.update(on_unavailable="DEFAULT", default=default)
    return p


def constant(value):
    return {"kind": "CONSTANT", "value": deepcopy(value)}


def upstream(node_id, output="result"):
    return {"kind": "UPSTREAM_OUTPUT", "node_id": node_id, "output": output}


def node(
    node_id,
    kind,
    capability="com.example.execution.mock",
    inputs=None,
    outputs=None,
    bindings=None,
    config=None,
    subject=None,
    criterion=None,
    members=None,
):
    inputs, outputs, bindings = (
        deepcopy(inputs or []),
        deepcopy(outputs or []),
        deepcopy(bindings or {}),
    )
    if kind in ("EVALUATE", "AGGREGATE"):
        inputs += [port("subject", {"type": "object"}), port("criterion", {"type": "object"})]
        bindings.update(
            subject=constant(subject or SUBJECT), criterion=constant(criterion or CRITERION)
        )
        outputs += [{"name": "result", "schema": {"type": "object"}, "role": "RESULT"}]
    if kind == "AGGREGATE":
        inputs.append(port("members", {"type": "array", "items": {"type": "string"}}))
        bindings["members"] = constant(list(members or []))
    if kind == "CONTROL":
        outputs += [{"name": "decision", "schema": {"type": "object"}, "role": "DECISION"}]
    return {
        "id": node_id,
        "kind": kind,
        "operation": {"capability_id": capability, "capability_version": "1"},
        "inputs": inputs,
        "outputs": outputs,
        "bindings": bindings,
        "config": deepcopy(config or {}),
        "aggregate_inputs": list(members or []),
    }


def definition(nodes, edges=None, run_inputs=None, subject=None, criterion=None):
    return {
        "protocol": "draft",
        "id": "prose-criterion",
        "version": "1",
        "subject": deepcopy(subject or SUBJECT),
        "criterion": deepcopy(criterion or CRITERION),
        "judgment_schema": {},
        "run_inputs": deepcopy(run_inputs or []),
        "execution_policy": {
            "activation": {"executor_ref": "MANUAL"},
            "selection": {"executor_ref": "EXPLICIT"},
            "admission": {"strategy": "ALWAYS"},
        },
        "graph": {"nodes": nodes, "edges": edges or []},
    }


def edge(a, b):
    return {"from_node": a, "to_node": b}


def information(name, schema=None):
    return {"name": name, "schema": {} if schema is None else schema, "role": "INFORMATION"}


def upgrade_definition(old):
    d = deepcopy(old)
    supplied = {}
    for n in d["graph"]["nodes"]:
        old_id = n.pop("executor_ref")
        capability = (
            "openverify.aggregate"
            if old_id == "standard.aggregate"
            else "com.example." + old_id.replace("-", "_")
        )
        n.update(
            operation={"capability_id": capability, "capability_version": "1"},
            inputs=[],
            outputs=[],
            bindings={},
            aggregate_inputs=[],
        )
        if n["kind"] in ("EVALUATE", "AGGREGATE"):
            n["inputs"] += [
                port("subject", {"type": "object"}),
                port("criterion", {"type": "object"}),
            ]
            n["bindings"].update(subject=constant(d["subject"]), criterion=constant(d["criterion"]))
            n["outputs"].append({"name": "result", "schema": {"type": "object"}, "role": "RESULT"})
        if n["kind"] == "CONTROL":
            n["outputs"].append(
                {"name": "decision", "schema": {"type": "object"}, "role": "DECISION"}
            )
        if n["kind"] == "DERIVE":
            n["outputs"].append(information(n["config"]["output_key"], {"type": "integer"}))
        if "key" in n.get("config", {}):
            key = n["config"]["key"]
            typ = "string" if old_id in ("demo.regex", "demo.length") else "number"
            n["inputs"].append(port(key, {"type": typ}))
            producer = next(
                (
                    x
                    for x in d["graph"]["nodes"]
                    if x["kind"] == "DERIVE" and x.get("config", {}).get("output_key") == key
                ),
                None,
            )
            if producer:
                n["bindings"][key] = upstream(producer["id"], key)
            else:
                n["bindings"][key] = {"kind": "RUN_INPUT", "name": key}
                supplied[key] = port(key, {"type": typ})
    by_id = {n["id"]: n for n in d["graph"]["nodes"]}
    for n in d["graph"]["nodes"]:
        if n["kind"] in ("AGGREGATE", "CONTROL"):
            for e in d["graph"]["edges"]:
                if (
                    e["to_node"] == n["id"]
                    and e["from_node"] in by_id
                    and by_id[e["from_node"]]["kind"] in ("EVALUATE", "AGGREGATE")
                ):
                    name = e["from_node"]
                    n["inputs"].append(port(name, {"type": "object"}))
                    n["bindings"][name] = upstream(name)
                    if n["kind"] == "AGGREGATE":
                        n["aggregate_inputs"].append(name)
    for n in d["graph"]["nodes"]:
        if n["kind"] == "AGGREGATE":
            n["inputs"].append(port("members", {"type": "array", "items": {"type": "string"}}))
            n["bindings"]["members"] = constant(n["aggregate_inputs"])
    for e in d["graph"]["edges"]:
        if e.get("guard"):
            g = e["guard"]
            role = "decision" if g["field"].startswith("decision_") else "result"
            field = g["field"].removeprefix("decision_")
            e["guard"] = {
                "source": upstream(g["node_id"], role),
                "pointer": "/" + field,
                "value": g["value"],
            }
    d["run_inputs"] = list(supplied.values())
    return d
