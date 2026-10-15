"""Author a NEW semantic baseline from prose, schemas and independent tables.

This authoring tool refuses an existing release. It cannot update snapshots and
does not import or run OpenVerify. Run only before the expectation freeze commit.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from tools.golden.enumerate_graphs import explore, generated, labeled_dags
from tools.golden.oracle import (DECISIONS, EXCEPTIONAL, KINDS, LIFECYCLE, MISSING, REDUCERS,
    opportunity, projection, reduce_results, result, result_axes, result_error)
from tools.golden.provider_oracle import encode_frame, trace_error

ROOT = Path(__file__).resolve().parents[2]
REVISION = "efe9abdfabbe913e9633687721690af47ef61b26"
BASE = ROOT / "conformance/golden/versions" / ("draft-" + REVISION[:7])
RELEASE = "0.1.0"
CASES = []
INPUTS = defaultdict(dict)
EXPECTED = defaultdict(dict)
FEATURES = {}


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def feature(identity, reference, profile="vcp", status="supported", obligations=()):
    FEATURES[identity] = {"feature_id": identity, "normative_reference": reference,
        "protocol_version": "0.1" if profile == "provider" else "draft",
        "normative_support": status, "implementation_support": "documented" if status == "supported" else status,
        "implementation_evidence": "published documentation at " + REVISION,
        "profiles": [profile], "obligations": list(obligations),
        "valid_case_ids": [], "invalid_case_ids": [], "transition_case_ids": [],
        "boundary_case_ids": [], "interaction_case_ids": []}


def add(identity, operation, payload, expected, features, profile="vcp", category="vcp/results", marks=()):
    if identity in INPUTS[category]:
        raise ValueError("duplicate case " + identity)
    INPUTS[category][identity] = payload
    EXPECTED[category][identity] = expected
    valid = not expected.get("error_code") and not expected.get("reject") and expected.get("accept", True)
    case = {"id": identity, "operation": operation, "profile": profile, "category": category,
        "input_ref": "fixtures/" + category + ".json#/" + identity,
        "expected_ref": "expected/" + category + ".json#/" + identity,
        "feature_ids": features, "marks": list(marks), "valid": valid,
        "references": sorted({FEATURES[f]["normative_reference"] for f in features})}
    CASES.append(case)
    for f in features:
        row = FEATURES[f]
        row["valid_case_ids" if valid else "invalid_case_ids"].append(identity)
        for mark in marks:
            key = {"transition": "transition_case_ids", "boundary": "boundary_case_ids", "interaction": "interaction_case_ids"}.get(mark)
            if key:
                row[key].append(identity)


def port(name, schema=True, required=True, default=MISSING):
    d = {"name": name, "schema": schema, "required": required,
         "on_unavailable": "BLOCK" if required else "OMIT" if default is MISSING else "DEFAULT"}
    if default is not MISSING:
        d["default"] = {"kind": "CONSTANT", "value": default}
    return d


SUBJECT = {"id": "golden.subject", "type": "application/json", "locator": {"host_supplied": True}}
CRITERION = {"id": "golden.criterion", "description": "The explicitly supplied deterministic criterion holds"}
EXTERNAL = {"id": "external.reference", "type": "application/json", "locator": {"uri": "https://invalid.example/no-fetch"}}
USAGE = {"com.example.calls": {"kind": "EXACT", "unit": "call", "value": 2}}


def constant(value):
    return {"kind": "CONSTANT", "value": value}


def upstream(node, output="value"):
    return {"kind": "UPSTREAM_OUTPUT", "node_id": node, "output": output}


def node(identity, kind="DERIVE", inputs=None, bindings=None, outputs=None, config=None, capability=None):
    inputs, bindings = list(inputs or []), dict(bindings or {})
    if kind in ("EVALUATE", "AGGREGATE"):
        inputs += [port("subject", {"type": "object"}), port("criterion", {"type": "object"})]
        bindings.update(subject=constant(SUBJECT), criterion=constant(CRITERION))
    if outputs is None:
        outputs = [{"name": "value", "schema": True, "role": "INFORMATION"}] if kind == "DERIVE" else [{"name": "decision" if kind == "CONTROL" else "result", "schema": True, "role": "DECISION" if kind == "CONTROL" else "RESULT"}]
    return {"id": identity, "kind": kind, "operation": {"capability_id": capability or "com.example.golden." + kind.lower(), "capability_version": "1"},
        "inputs": inputs, "bindings": bindings, "outputs": outputs, "config": config or {}}


def definition(nodes, edges=(), inputs=()):
    return {"protocol": "draft", "id": "golden.definition", "version": "1", "subject": deepcopy(SUBJECT), "criterion": deepcopy(CRITERION),
        "judgment_schema": True, "run_inputs": list(inputs), "graph": {"nodes": list(nodes), "edges": [edge(*e) if isinstance(e, tuple) else e for e in edges]},
        "execution_policy": {"activation": {"executor_ref": "MANUAL"}, "selection": {"executor_ref": "EXPLICIT"}, "admission": {"strategy": "ALWAYS"}}}


def edge(a, b, guard=None):
    e = {"from_node": a, "to_node": b}
    if guard is not None:
        e["guard"] = guard
    return e


def behavior(outputs=None, **kwargs):
    return {"outputs": outputs or {}, **kwargs}


def success(n, outputs):
    d = {"state": "SUCCESS", "information": {p["name"]: outputs[p["name"]] for p in n["outputs"] if p["role"] == "INFORMATION"}}
    if "result" in outputs:
        d["result"] = outputs["result"]
    if "decision" in outputs:
        d["decision"] = outputs["decision"]
    return d


def nonexecution(reason):
    disposition, state = LIFECYCLE[reason]
    return {"state": state, "reason": reason, "information": {}, "result": {"protocol": "draft", "disposition": disposition, "output": {"reason": reason}},
        "absent": ["provider_binding", "executor_ref", "executor_version", "observation", "decision"]}


def scenario(nodes, edges, behaviors, expectations, inputs=None, declarations=(), **options):
    return {"definition": definition(nodes, edges, declarations), "inputs": inputs or {},
        "behaviors": behaviors, "nodes": expectations, **options}


def register_features():
    rows = {
        "result.axes": "spec/draft/result.md", "result.observations": "spec/draft/result.md",
        "result.projection": "spec/draft/result.md", "json.types": "spec/draft/wire-format.md",
        "wire.strict": "spec/draft/wire-format.md", "definitions": "spec/draft/meaning.md",
        "evidence": "spec/draft/knowledge.md", "extensions": "spec/draft/extensions.md",
        "schemas.self_contained": "spec/draft/dataflow.md", "resources": "spec/draft/resources.md",
        "semantic.binding": "spec/draft/dataflow.md", "guards": "spec/draft/dataflow.md",
        "graphs.topology": "spec/draft/composition.md", "graphs.interleavings": "spec/draft/lifecycle.md",
        "graphs.metamorphic": "spec/draft/composition.md", "provenance": "spec/draft/provenance.md",
        "aggregate.membership": "spec/draft/dataflow.md", "reducer.handling": "spec/draft/aggregation.md",
        "policies": "spec/draft/execution-policy.md", "lifecycle.precedence": "spec/draft/lifecycle.md",
    }
    for identity, ref in rows.items():
        feature(identity, ref)
    for kind in KINDS:
        feature("node." + kind, "spec/draft/dataflow.md", "relay-local")
    for source in ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE", "UPSTREAM_OUTPUT"):
        feature("source." + source, "spec/draft/dataflow.md", "relay-local")
    for availability in ("AVAILABLE", "ABSENT", "PRODUCER_NOT_EXECUTED", "PRODUCER_ERROR", "OUTPUT_MISSING", "INVALID"):
        feature("availability." + availability, "spec/draft/dataflow.md", "relay-local")
    for reducer in (*REDUCERS, "CUSTOM"):
        feature("reducer." + reducer, "spec/draft/aggregation.md", "relay-local")
    for decision in DECISIONS:
        feature("control." + decision, "spec/draft/lifecycle.md", "relay-local")
    for phase in ("activation", "selection", "admission"):
        feature("policy." + phase, "spec/draft/execution-policy.md", "relay-local")
    for topic in ("manifests", "negotiation", "invocation", "events", "lifecycle", "cancellation", "deadlines", "faults", "framing", "correlation"):
        feature("provider." + topic, "provider-contract/spec/draft/" + ("transports" if topic in ("framing", "correlation") else "capabilities" if topic == "manifests" else "versioning" if topic == "negotiation" else "lifecycle") + ".md", "provider")
    for topic in ("binding", "concurrency", "isolation", "cancellation", "timeout", "security", "observer_failure", "store_failure"):
        feature("relay." + topic, "docs/relay/architecture.md" if topic != "security" else "docs/relay/security.md", "relay-local")
    for name in ("ProviderCatalog", "ProviderBinder", "ExecutionDriver", "ProviderTransport", "RecordStore", "EventObserver"):
        feature("port." + name, "docs/relay/architecture.md", "relay-local", obligations=("default", "replacement", "valid", "invalid", "exception", "isolation"))
    for entry in ("python", "cli", "mcp", "http", "guardrail", "multi_agent"):
        feature("integration." + entry, "docs/relay/integration.md", "integration")
    for capability in ("read_text", "read_file", "select_files", "git_scope", "candidate_unchanged", "ruff", "pytest", "astgrep", "scope", "no_findings", "text", "json_parse", "schema", "action_policy", "gate", "command", "command_check", "aggregate"):
        feature("standard." + capability, "docs/relay/providers.md", "integration")
    for future in ("CYCLES", "DYNAMIC_EXPANSION", "ITERATION"):
        feature("unsupported." + future, "spec/draft/composition.md", status="unsupported")
    for name in ("numeric_portability", "sampling_identity", "parallel_cancellation_provenance", "transport_policy_provenance", "authenticity"):
        feature("open." + name, "spec/draft/open-questions.md", status="ambiguous")


def result_cases():
    valid = 0
    for i, r in enumerate(result_axes()):
        code = result_error(r)
        valid += code is None
        expected = {"accept": not code, "error_code": code} if code else {"accept": True, "preserve": r, "projection": projection(r)}
        add(f"result.axes.{i:04d}", "parse_result", r, expected, ["result.axes", "result.projection"], marks=("boundary",))
    representatives = [result(x) for x in ("PASS", "FAIL", "KNOWN", "UNKNOWN", "ERROR", "NOT_APPLICABLE", "SKIP", "DEFERRED", "CANCELLED")]
    observations = {"judgment": None, "score": 0.5, "severity": {"domain": "unresolved.domain", "label": "opaque"},
        "evidence": [{"structured_data": {}}], "output": None, "usage": USAGE,
        "metadata": {"type_sensitive": [True, 1, False, 0]}, "extensions": [{"namespace": "com.example:golden", "version": "1", "required": False, "data": [None, True, 1]}]}
    for state, r in enumerate(representatives):
        for bits in itertools.product((False, True), repeat=len(observations)):
            d = deepcopy(r)
            d.update({k: deepcopy(v) for (k, v), chosen in zip(observations.items(), bits) if chosen})
            code = result_error(d)
            index = sum(int(b) << i for i, b in enumerate(bits))
            add(f"result.observations.{state}.{index:03d}", "parse_result", d,
                {"accept": False, "error_code": code} if code else {"accept": True, "preserve": d, "projection": projection(d)},
                ["result.observations", "json.types"], marks=("interaction",))
    partitions = [None, False, True, 0, 1, 0.0, 0.25, "", "nonempty", [], [0, False], {}, {"a": {"b": [True, 1]}}, [[None], ["é", "😀"]], "日本語\u0000", 9007199254740991, -9007199254740991, 1e-300]
    for i, v in enumerate(partitions):
        for field in ("judgment", "output"):
            r = result("KNOWN", **{field: v})
            add(f"result.partition.{field}.{i}", "parse_result", r, {"accept": True, "preserve": r, "projection": None}, ["json.types", "result.observations"], marks=("boundary",))
    for i, score in enumerate([False, True, "0.5", -0.01, 1.01, 0, 1, 0.5, None]):
        r = result("KNOWN", score=score); code = result_error(r)
        add(f"result.score.{i}", "parse_result", r, {"error_code": code} if code else {"accept": True, "preserve": r, "projection": None}, ["result.axes"], marks=("boundary",))
    for i, raw in enumerate(['{"protocol":"draft","protocol":"draft","disposition":"SKIPPED"}', '{"protocol":"draft","disposition":"EXECUTED","score":NaN}', '{"a":Infinity}', '{bad', '[]', 'null']):
        add(f"wire.invalid.{i}", "parse_raw", {"object_type": "result", "raw": raw}, {"error_code": "PROTOCOL_JSON" if i < 4 else "PROTOCOL_STRUCTURE"}, ["wire.strict"])
    return {"total": i + 1 if False else 1024, "valid": valid, "invalid": 1024 - valid, "optional_presence_masks": 256, "representative_result_states": len(representatives)}


def wire_cases():
    for decision in DECISIONS:
        for dest in (MISSING, None, "target", ""):
            obj = {"protocol": "draft", "kind": decision}
            if dest is not MISSING:
                obj["destination"] = dest
            code = "PROTOCOL_STRUCTURE" if dest == "" else "DECISION_STATE" if (decision == "ROUTE") != (isinstance(dest, str) and bool(dest)) else None
            exp = {"reject":True,"blocked_error_category":"Decision invariant error code is not specified in conformance.md"} if code == "DECISION_STATE" else {"error_code":code} if code else {"accept":True}
            add(f"decision.{decision}.{['missing','null','target','empty'][(MISSING,None,'target','').index(dest)]}", "parse_object", {"object_type": "decision", "value": obj}, exp, ["control." + decision])
    for kind in ("EXACT", "ESTIMATED", "RANGE", "UNKNOWN"):
        for fields in ({}, {"value": 0}, {"value": 2}, {"value": True}, {"value": -1}, {"minimum": 0, "maximum": 2}, {"minimum": 2, "maximum": 1}, {"value": 1, "minimum": 0, "maximum": 2}):
            obj = {"unit": "custom", "kind": kind, **fields}
            structural = any(isinstance(v, bool) or isinstance(v, (int, float)) and v < 0 for v in fields.values())
            valid = set(fields) == {"value"} if kind in ("EXACT", "ESTIMATED") else set(fields) == {"minimum", "maximum"} and fields["minimum"] <= fields["maximum"] if kind == "RANGE" else not fields
            add(f"resource.{kind}.{len(INPUTS['vcp/resources'])}", "parse_object", {"object_type": "resource", "value": obj}, {"accept": True} if valid and not structural else {"error_code": "PROTOCOL_STRUCTURE" if structural else "RESOURCE_MEASUREMENT"}, ["resources"], category="vcp/resources", marks=("boundary",))
    for i, ev in enumerate([{}, {"id": "alone"}, {"message": None}, {"structured_data": {}}, {"structured_data": []}, {"locator": 0}, {"message": "supports"}, {"message": ""}]):
        add(f"evidence.{i}", "parse_object", {"object_type": "evidence", "value": ev}, {"accept": True} if i in (3,4,5,6) else {"error_code": "PROTOCOL_STRUCTURE" if i == 7 else "EVIDENCE_EMPTY"}, ["evidence"], category="vcp/provenance")
    for required in (False, True):
        r = result("PASS", extensions=[{"namespace": "com.example:future", "version": "1", "required": required, "data": {"x": [False, 0]}}])
        add(f"extension.required.{required}", "parse_result", r, {"error_code": "EXTENSION_UNSUPPORTED"} if required else {"accept": True, "preserve": r, "projection": "PASS"}, ["extensions"])


def definition_cases():
    for kind in KINDS:
        n = node("n", kind)
        if kind == "AGGREGATE":
            n = node("n", kind, [port("member"), port("members", {"type": "array"})], {"member": upstream("p", "result"), "members": constant(["member"])})
            n["aggregate_inputs"] = ["member"]
            nodes, edges = [node("p", "EVALUATE"), n], [("p", "n")]
        else:
            nodes, edges = [n], []
        d = definition(nodes, edges)
        add("definition.minimum." + kind, "parse_definition", d, {"accept": True}, ["definitions", "node." + kind], category="vcp/definitions")
        full = deepcopy(d)
        full.update(metadata={"note": "full"}, satisfaction_mapping={"id": "unexecuted"}, extensions=[])
        full["graph"]["nodes"][-1].update(resource_estimate={"energy": {"kind": "ESTIMATED", "unit": "joule", "value": 3}}, config_schema=True, metadata={"kind": kind})
        add("definition.full." + kind, "parse_definition", full, {"accept": True}, ["definitions", "node." + kind], category="vcp/definitions")
    base = definition([node("a"), node("b", inputs=[port("v")], bindings={"v": upstream("a")})], [("a", "b")])
    mutations = []
    def change(identity, code, fn, feat="definitions"):
        d = deepcopy(base); fn(d); mutations.append((identity, code, d, feat))
    change("duplicate_node", "GRAPH_DUPLICATE", lambda d: d["graph"]["nodes"].append(deepcopy(d["graph"]["nodes"][0])))
    change("missing_endpoint", "GRAPH_REFERENCE", lambda d: d["graph"]["edges"].append(edge("missing", "b")))
    change("duplicate_edge", "GRAPH_DUPLICATE", lambda d: d["graph"]["edges"].append(edge("a", "b")))
    change("self", "GRAPH_UNSUPPORTED", lambda d: d["graph"]["edges"].append(edge("a", "a")), "unsupported.CYCLES")
    change("cycle", "GRAPH_UNSUPPORTED", lambda d: d["graph"]["edges"].append(edge("b", "a")), "unsupported.CYCLES")
    change("expansion", "GRAPH_UNSUPPORTED", lambda d: d["graph"].update(features=["DYNAMIC_EXPANSION"]), "unsupported.DYNAMIC_EXPANSION")
    change("iteration", "GRAPH_UNSUPPORTED", lambda d: d["graph"].update(features=["CYCLES"]), "unsupported.ITERATION")
    change("no_order_path", "DATAFLOW_BINDING", lambda d: d["graph"].update(edges=[]), "source.UPSTREAM_OUTPUT")
    change("wrong_port", "DATAFLOW_BINDING", lambda d: d["graph"]["nodes"][1]["bindings"]["v"].update(output="missing"), "source.UPSTREAM_OUTPUT")
    change("undeclared_target", "DATAFLOW_BINDING", lambda d: d["graph"]["nodes"][0]["bindings"].update(other=constant(1)))
    change("required_unbound", "DATAFLOW_BINDING", lambda d: d["graph"]["nodes"][1].update(bindings={}))
    change("wrong_const", "DATAFLOW_SCHEMA", lambda d: d["graph"]["nodes"][1].update(inputs=[port("v", {"type": "string"})], bindings={"v": constant(False)}), "json.types")
    change("wrong_config", "DATAFLOW_CONFIG", lambda d: d["graph"]["nodes"][0].update(config_schema=False), "schemas.self_contained")
    change("missing_run_declaration", "DATAFLOW_BINDING", lambda d: d["graph"]["nodes"][1].update(bindings={"v": {"kind": "RUN_INPUT", "name": "missing"}}))
    change("wrong_protocol", "PROTOCOL_VERSION", lambda d: d.update(protocol="1.0"))
    change("unknown_core", "PROTOCOL_STRUCTURE", lambda d: d.update(arbitrary=True), "wire.strict")
    for identity, code, d, feat in mutations:
        add("definition.invalid." + identity, "parse_definition", d, {"error_code": code}, [feat], category="vcp/definitions")
    for i, schema in enumerate([{"$ref": "https://invalid.example/schema"}, {"$defs": {"x": {"$id": "nested", "type": "string"}}}, {"$dynamicRef": "#x"}, {"$ref": "#/$defs/missing"}, {"$anchor": "x"}]):
        d = deepcopy(base); d["judgment_schema"] = schema
        add(f"definition.unsupported_schema.{i}", "parse_definition", d, {"error_code": "SCHEMA_UNSUPPORTED"}, ["schemas.self_contained"], category="vcp/definitions")
    for schema in (True, {"$defs": {"x": {"type": "string"}}, "$ref": "#/$defs/x"}, {"const": True}, {"format": "unknown-annotation"}):
        d = deepcopy(base); d["judgment_schema"] = schema
        add(f"definition.schema.valid.{len(INPUTS['vcp/definitions'])}", "parse_definition", d, {"accept": True}, ["schemas.self_contained"], category="vcp/definitions")
    for kind in ("EVALUATE","AGGREGATE"):
        d=definition([node("evaluation","EVALUATE")])
        d["graph"]["nodes"][0]["bindings"]["subject"]=constant({"id":"unrelated","type":"text/plain","locator":None})
        add("semantic.subject_mismatch."+kind,"parse_definition",d,{"error_code":"SEMANTIC_BINDING"},["semantic.binding"],category="vcp/definitions")


def graph_cases():
    counts = Counter(); states = transitions = 0
    for i, (n, edges) in enumerate(labeled_dags(4)):
        counts[n] += 1
        nodes = [node(str(j)) for j in range(n)]
        outputs = {str(j): {"value": j} for j in range(n)}
        sc = scenario(nodes, [(str(a), str(b)) for a, b in edges], {k: behavior(v) for k,v in outputs.items()}, {x["id"]: success(x, outputs[x["id"]]) for x in nodes})
        add(f"dag.labeled.{i:04d}", "run", sc, {"nodes": sc["nodes"]}, ["graphs.topology", "node.DERIVE"], "relay-local", "relay/graphs", ("interaction",))
        if n <= 3:
            exploration = explore(n, edges)
            states += len(exploration["states"]); transitions += len(exploration["transitions"])
            add(f"scheduler.abstract.{i:04d}", "abstract_scheduler", {"n": n, "edges": edges}, exploration, ["graphs.interleavings"], "relay-local", "relay/scheduling", ("transition",))
    for i, (n, edges) in enumerate(generated(71717)):
        nodes = [node(str(j)) for j in range(n)]
        sc = scenario(nodes, [(str(a),str(b)) for a,b in edges], {str(j): behavior({"value": j}) for j in range(n)}, {str(j): success(nodes[j], {"value": j}) for j in range(n)})
        add(f"dag.seed71717.{i}", "metamorphic_run", sc, {"nodes": sc["nodes"], "variants": ["reverse_nodes", "reverse_edges", "irrelevant_node"]}, ["graphs.metamorphic"], "relay-local", "relay/graphs", ("interaction",))
    assignments = 0
    for n, edges in labeled_dags(2):
        if not n:
            continue
        for assignment in itertools.product(KINDS, repeat=n):
            # An Aggregate requires a strict ancestor Result member. Inapplicable
            # assignments are explicit invalid definitions, not dropped silently.
            nodes = [node(str(j), kind) for j,kind in enumerate(assignment)]
            valid = "AGGREGATE" not in assignment
            sc = scenario(nodes, [(str(a),str(b)) for a,b in edges], {}, {})
            for x in nodes:
                out = {"value": x["id"]} if x["kind"] == "DERIVE" else {"decision": {"protocol": "draft", "kind": "CONTINUE"}} if x["kind"] == "CONTROL" else {"result": result("PASS")}
                sc["behaviors"][x["id"]] = behavior(out)
                sc["nodes"][x["id"]] = success(x, out)
            add(f"dag.kinds.{assignments:03d}", "run" if valid else "parse_definition", sc if valid else sc["definition"], {"nodes": sc["nodes"]} if valid else {"error_code": "DATAFLOW_BINDING"}, ["graphs.topology", *sorted({"node."+x for x in assignment})], "relay-local", "relay/graphs")
            assignments += 1
    return {"all_labeled_dags_bound": 4, "topology_counts_by_n": dict(counts), "topologies": sum(counts.values()), "kind_assignment_bound": 2, "kind_assignments_including_inapplicable": assignments, "abstract_bound": 3, "abstract_states": states, "abstract_transitions": transitions, "random_seed": 71717, "random_graphs": 32, "random_node_bound": 12, "terminal_outcome_coloring": "separate Result cases; not multiplied into scheduler states"}


def reducer_cases():
    domain = {"id": "golden.severity", "levels": [{"label": "low", "rank": 1}, {"label": "high", "rank": 2}]}
    all_ignore = dict.fromkeys(EXCEPTIONAL, "IGNORE")
    total = 0
    for name in REDUCERS:
        base = [result("PASS"), result("FAIL")]
        if name in REDUCERS[3:7]:
            base = [result("KNOWN", score=0), result("KNOWN", score=1)]
        if name == "WORST_SEVERITY":
            base = [result("KNOWN", severity={"domain": domain["id"], "label": "low"}), result("KNOWN", severity={"domain": domain["id"], "label": "high"})]
        sequences = [[], [base[0]], base, [base[0],base[0]], [base[1],base[1]], [base[1],base[0]], [base[0],base[1],base[0]]]
        sequences += [[base[0], result(e)] for e in EXCEPTIONAL if e != "MISSING"] + [[base[0],result("KNOWN")]]
        for j, seq in enumerate(sequences):
            # Enumerate all 2^7 handling configurations for each exceptional member.
            masks = itertools.product(("REJECT", "IGNORE"), repeat=7) if j >= 7 else [tuple("REJECT" for _ in EXCEPTIONAL), tuple("IGNORE" for _ in EXCEPTIONAL)]
            for k, choices in enumerate(masks):
                config = {"reducer": name, "handling": dict(zip(EXCEPTIONAL, choices))}
                if name == "WEIGHTED_AVERAGE":
                    config["weights"] = [1] * len(seq)
                if name == "WORST_SEVERITY":
                    config["severity_domain"] = domain
                exp = reduce_results(name, seq, config)
                # Three-member numeric means (1/3,2/3) have no portable rounding
                # rule. They are excluded from exact wire comparisons explicitly.
                if j == 6 and name in ("AVERAGE", "WEIGHTED_AVERAGE"):
                    exp = {"blocked_by_spec": "numeric_portability", "mathematical_value": "1/3"}
                add(f"reducer.{name}.{j}.{k}", "reducer_graph", {"reducer": name, "members": seq, "config": config}, exp, ["reducer."+name,"reducer.handling","aggregate.membership"], "relay-local", "vcp/reducers", ("interaction",))
                total += 1
    for identity, seq, weights in [("exact_075", [result("KNOWN",score=0),result("KNOWN",score=1)], [1,3]), ("zero", [result("KNOWN",score=0)], [0]), ("negative", [result("KNOWN",score=0)], [-1]), ("count", [result("KNOWN",score=0)], []), ("filtered_identity", [result("ERROR"),result("KNOWN",score=0.75)], [100,1])]:
        config = {"reducer": "WEIGHTED_AVERAGE", "handling": all_ignore, "weights": weights}
        add("weighted."+identity, "reducer_graph", {"reducer":"WEIGHTED_AVERAGE","members":seq,"config":config}, reduce_results("WEIGHTED_AVERAGE", seq, config), ["reducer.WEIGHTED_AVERAGE","aggregate.membership"], "relay-local", "vcp/reducers", ("boundary",))
    for variant in ("equal_ranks", "invalid_label", "wrong_domain", "integral_ranks"):
        dom = deepcopy(domain); seq = [result("KNOWN",severity={"domain":dom["id"],"label":"low"})]
        if variant == "equal_ranks": dom["levels"][1]["rank"] = 1
        if variant == "invalid_label": seq[0]["severity"]["label"] = "missing"
        if variant == "wrong_domain": seq[0]["severity"]["domain"] = "other"
        if variant == "integral_ranks": dom["levels"][0]["rank"] = 1.0
        config = {"reducer":"WORST_SEVERITY","handling":all_ignore,"severity_domain":dom}
        add("severity."+variant,"reducer_graph",{"reducer":"WORST_SEVERITY","members":seq,"config":config},reduce_results("WORST_SEVERITY",seq,config),["reducer.WORST_SEVERITY"],"relay-local","vcp/reducers",("boundary",))
    return {"standard_reducer_generated_cases": total, "handling_masks_per_exceptional_partition": 128}


def input_cases():
    for kind in KINDS:
        for source_kind in ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE", "UPSTREAM_OUTPUT"):
            for partition, val in enumerate([None, False, 0, "é", [], {"nested": [True,1]}]):
                source = constant(val) if source_kind == "CONSTANT" else {"kind":"RUN_INPUT","name":"data"} if source_kind == "RUN_INPUT" else {"kind":"EXTERNAL_REFERENCE","reference":EXTERNAL} if source_kind == "EXTERNAL_REFERENCE" else upstream("producer")
                actual = EXTERNAL if source_kind == "EXTERNAL_REFERENCE" else val
                consumer = node("consumer",kind,[port("data")],{"data":source})
                nodes, edges, behaviors, expected = [], [], {}, {}
                if source_kind == "UPSTREAM_OUTPUT":
                    producer = node("producer"); nodes.append(producer); edges.append(("producer","consumer"))
                    behaviors["producer"] = behavior({"value":val}); expected["producer"] = success(producer,{"value":val})
                if kind == "AGGREGATE":
                    producer = node("member","EVALUATE"); nodes.append(producer); edges.append(("member","consumer"))
                    consumer["inputs"] += [port("item"),port("members")]
                    consumer["bindings"].update(item=upstream("member","result"),members=constant(["item"]))
                    consumer["aggregate_inputs"] = ["item"]
                    behaviors["member"] = behavior({"result":result("PASS")}); expected["member"] = success(producer,{"result":result("PASS")})
                nodes.append(consumer)
                outputs = {"value":actual} if kind == "DERIVE" else {"decision":{"protocol":"draft","kind":"CONTINUE"}} if kind == "CONTROL" else {"result":result("PASS")}
                behaviors["consumer"] = behavior(outputs); expected["consumer"] = success(consumer,outputs)
                sc = scenario(nodes,edges,behaviors,expected,{"data":val} if source_kind == "RUN_INPUT" else {}, [port("data")] if source_kind == "RUN_INPUT" else [])
                add(f"binding.{kind}.{source_kind}.{partition}","run",sc,{"nodes":expected},["node."+kind,"source."+source_kind,"availability.AVAILABLE","json.types"],"relay-local","vcp/inputs",("interaction",))
    for mode in ("OMIT","DEFAULT","BLOCK"):
        optional = port("data",required=mode == "BLOCK",default=None if mode == "DEFAULT" else MISSING)
        n = node("n",inputs=[optional],bindings={"data":{"kind":"RUN_INPUT","name":"data"}})
        sc = scenario([n],[],{"n":behavior({"value":None})},{"n": nonexecution("INPUT_UNAVAILABLE") if mode == "BLOCK" else success(n,{"value":None})}, declarations=[port("data",required=False)])
        add("input.absent."+mode,"run",sc,{"nodes":sc["nodes"]},["availability.ABSENT","source.RUN_INPUT"],"relay-local","vcp/inputs",("boundary",))
    for error in ("missing", "wrong_type", "undeclared"):
        n = node("n"); sc = scenario([n],[],{"n":behavior({"value":1})},{}, {"data":False} if error == "wrong_type" else {"unknown":1} if error == "undeclared" else {}, [port("data",{"type":"string"})])
        add("input.reject."+error,"run",sc,{"error_code":"RUN_INPUT"},["source.RUN_INPUT"],"relay-local","vcp/inputs")
    for producer_state in ("ERROR","SKIP","DEFERRED","CANCELLED","OUTPUT_MISSING","INVALID"):
        p = node("p"); c = node("c",inputs=[port("data")],bindings={"data":upstream("p")})
        if producer_state in ("SKIP","DEFERRED","CANCELLED"):
            # An invoked provider may NOT supply these to masquerade as lifecycle.
            p = node("p","EVALUATE"); p["outputs"].append({"name":"value","schema":True,"role":"INFORMATION"})
            pb = behavior({"result":result(producer_state),"value":"must-not-leak"})
        elif producer_state == "ERROR": pb = behavior(error={"code":"com.example.failed","message":"deliberate"},usage=USAGE)
        elif producer_state == "OUTPUT_MISSING": pb = behavior({})
        else: p["outputs"][0]["schema"] = {"type":"string"}; pb=behavior({"value":False})
        exp = {"p":{"state":"ERROR","information":{},"result":{"protocol":"draft","disposition":"EXECUTED","execution_outcome":"ERROR"}},"c":nonexecution("INPUT_UNAVAILABLE")}
        sc = scenario([p,c],[("p","c")],{"p":pb,"c":behavior({"value":"stale"})},exp)
        add("producer.failure."+producer_state,"run",sc,{"nodes":exp},["availability.PRODUCER_ERROR","availability.INVALID" if producer_state == "INVALID" else "availability.OUTPUT_MISSING","node."+p["kind"]],"relay-local","vcp/dataflow",("interaction",))
    # Genuine nonexecution of an information producer: a false guard does not
    # disable descendants implicitly, but its unpublished information blocks them.
    r,p,c=node("root"),node("p"),node("c",inputs=[port("data")],bindings={"data":upstream("p")})
    exp={"root":success(r,{"value":1}),"p":nonexecution("GUARD_FALSE"),"c":nonexecution("INPUT_UNAVAILABLE")}
    sc=scenario([r,p,c],[edge("root","p",{"source":constant(False),"pointer":"","value":True}),edge("p","c")],{"root":behavior({"value":1}),"p":behavior({"value":"stale"}),"c":behavior({"value":"stale"})},exp)
    add("availability.producer_not_executed","run",sc,{"nodes":exp},["availability.PRODUCER_NOT_EXECUTED","guards"],"relay-local","vcp/dataflow",("interaction",))
    # A bookkeeping ERROR is itself an available RESULT-role value.
    p=node("p","EVALUATE"); c=node("c",inputs=[port("checked")],bindings={"checked":upstream("p","result")})
    exp={"p":{"state":"ERROR","information":{},"result":result("ERROR")},"c":success(c,{"value":"inspected error"})}
    sc=scenario([p,c],[("p","c")],{"p":behavior({"result":result("ERROR")}),"c":behavior({"value":"inspected error"})},exp)
    add("availability.error_result_available","run",sc,{"nodes":exp},["availability.AVAILABLE","availability.PRODUCER_ERROR"],"relay-local","vcp/dataflow",("interaction",))


def control_policy_cases():
    for decision in DECISIONS:
        c = node("control","CONTROL"); a,b,join = node("a"),node("b"),node("join")
        dec = {"protocol":"draft","kind":decision}
        if decision == "ROUTE": dec["destination"] = "a"
        behaviors = {"control":behavior({"decision":dec}), **{x["id"]:behavior({"value":x["id"]}) for x in (a,b,join)}}
        expected = {"control":success(c,{"decision":dec})}
        reason = {"STOP_SUCCESS":"CONTROL_STOP","STOP_FAILURE":"CONTROL_STOP","RETRY":"RETRY_REQUESTED","DEFER":"CONTROL_DEFER"}.get(decision)
        for x in (a,b,join):
            expected[x["id"]] = nonexecution(reason) if reason else nonexecution("ROUTE_EXCLUDED") if decision == "ROUTE" and x["id"] == "b" else success(x,{"value":x["id"]})
        sc = scenario([c,a,b,join],[("control","a"),("control","b"),("a","join"),("b","join")],behaviors,expected)
        add("control.graph."+decision,"run",sc,{"nodes":expected},["control."+decision,"lifecycle.precedence"],"relay-local","vcp/graph-control",("transition","interaction"))
    for value in (True,False,None):
        p,c = node("p"),node("c",inputs=[port("data")],bindings={"data":upstream("p")})
        guard = {"source":constant(value),"pointer":"","value":True}
        sc = scenario([p,c],[edge("p","c",guard)],{"p":behavior({"value":10}),"c":behavior({"value":10})},{"p":success(p,{"value":10}),"c":success(c,{"value":10}) if value is True else nonexecution("GUARD_FALSE")})
        add("guard.literal."+str(value),"run",sc,{"nodes":sc["nodes"]},["guards","json.types"],"relay-local","vcp/graph-control",("boundary",))
    p,c = node("p"),node("c",inputs=[port("data")],bindings={"data":upstream("p")})
    sc = scenario([p,c],[edge("p","c",{"source":upstream("p"),"pointer":"/missing","value":1})],{"p":behavior({"value":{}}),"c":behavior({"value":1})},{"p":success(p,{"value":{}}),"c":nonexecution("GUARD_FALSE")})
    add("guard.absent","run",sc,{"nodes":sc["nodes"]},["guards"],"relay-local","vcp/graph-control")
    for activation,selected,admission in itertools.product(("ACTIVATE","DO_NOT_ACTIVATE"),(True,False),("RUN","SKIP","DEFER")):
        n=node("n"); expected=opportunity(activation,selected,admission)
        sc=scenario([n],[],{"n":behavior({"value":1})},{"n":success(n,{"value":1}) if admission == "RUN" else nonexecution("ADMISSION_"+admission)},policies={"ACTIVATION":{"outcome":activation,"reason":"golden.activation"},"SELECTION":{"subjects":[SUBJECT] if selected else [],"reason":"golden.selection"},"ADMISSION":{"outcome":admission,"reason":"golden.admission"}})
        add(f"policy.{activation}.{selected}.{admission}","policy_run",sc,expected if not expected["occurrence"] else {"nodes":sc["nodes"]},["policies","policy.activation","policy.selection","policy.admission"],"relay-local","vcp/policies",("transition",))
    for probability in (0,1):
        n=node("n"); sc=scenario([n],[],{"n":behavior({"value":1})},{"n":nonexecution("ADMISSION_SKIP") if probability == 0 else success(n,{"value":1})})
        sc["definition"]["execution_policy"]["admission"]={"strategy":"PROBABILITY","probability":probability}
        add(f"policy.probability.{probability}","run",sc,{"nodes":sc["nodes"]},["policy.admission"],"relay-local","vcp/policies",("boundary",))


def comprehensive_cases():
    for label in ("PASS","FAIL","UNKNOWN","ERROR"):
        d1=node("D1",inputs=[port("run"),port("constant"),port("external")],bindings={"run":{"kind":"RUN_INPUT","name":"payload"},"constant":constant(3),"external":{"kind":"EXTERNAL_REFERENCE","reference":EXTERNAL}})
        d2=node("D2",inputs=[port("fixed")],bindings={"fixed":constant("branch-b")})
        e1=node("E1","EVALUATE",[port("data")],{"data":upstream("D1")}); e2=node("E2","EVALUATE",[port("data")],{"data":upstream("D2")})
        a1=node("A1","AGGREGATE",[port("first"),port("second"),port("members")],{"first":upstream("E1","result"),"second":upstream("E2","result"),"members":constant(["first","second"])},capability="openverify.aggregate",config={"reducer":"ALL","handling":dict.fromkeys(EXCEPTIONAL,"IGNORE")})
        a1["aggregate_inputs"]=["first","second"]
        c=node("C1","CONTROL",[port("checked")],{"checked":upstream("A1","result")})
        e3=node("E3","EVALUATE"); e4=node("E4","EVALUATE")
        a2=node("A2","AGGREGATE",[port("yes"),port("no"),port("members")],{"yes":upstream("E3","result"),"no":upstream("E4","result"),"members":constant(["yes","no"])},capability="com.example.golden.custom_aggregate")
        a2["aggregate_inputs"]=["yes","no"]
        selected="E4" if label == "FAIL" else "E3"
        dec={"protocol":"draft","kind":"ROUTE","destination":selected}
        aggregate=result("FAIL" if label == "FAIL" else "PASS",evidence=[])
        out={"D1":{"value":{"nested":[True,1,None]}},"D2":{"value":"branch-b"},"E1":{"result":result(label)},"E2":{"result":result("PASS")},"A1":{"result":aggregate},"C1":{"decision":dec},"E3":{"result":result("PASS")},"E4":{"result":result("FAIL")},"A2":{"result":result("FAIL" if label == "FAIL" else "PASS")}}
        nodes=[d1,d2,e1,e2,a1,c,e3,e4,a2]
        edges=[("D1","E1"),("D1","D2"),("D2","E2"),("E1","A1"),("E2","A1"),("A1","C1"),("C1","E3"),("C1","E4"),("E3","A2"),("E4","A2")]
        expected={n["id"]:success(n,out[n["id"]]) for n in nodes}
        expected["E4" if selected == "E3" else "E3"]=nonexecution("ROUTE_EXCLUDED")
        if label == "ERROR": expected["E1"]["state"]="ERROR"
        sc=scenario(nodes,edges,{k:behavior(v,usage=USAGE) for k,v in out.items() if k != "A1"},expected,{"payload":{"nested":[True,1,None]}},[port("payload",{"type":"object"})],description="Full multi-branch graph; D1->D2 is execution-only; A2 is custom; exact structural memberships are authored")
        add("comprehensive."+label,"run",sc,{"nodes":expected},["node."+k for k in KINDS]+["reducer.CUSTOM","aggregate.membership","provenance","resources"],"relay-local","relay/graphs",("interaction",))


def provider_cases():
    lifecycle={"streaming":True,"cancellation":True,"deadlines":True,"resource_reporting":True}
    cap={"capability_id":"com.example.golden.echo","capability_version":"1","input_schema":True,"config_schema":True,"output_schema":True,"lifecycle_features":lifecycle}
    manifest={"provider_id":"com.example.golden.provider","provider_version":"1","supported_contract_versions":["0.1"],"supported_vcp_versions":["draft"],"capabilities":[cap]}
    init={"supported_contract_versions":["0.1"],"supported_vcp_versions":["draft"]}
    inv={"invocation_id":"attempt-1","contract_version":"0.1","capability_id":cap["capability_id"],"capability_version":"1","input":{"v":[True,1,None]},"config":{},"vcp_version":"draft"}
    accept={"action":"accept","invocation":inv}
    completed={"action":"outcome","outcome":{"invocation_id":"attempt-1","state":"COMPLETED","output":{"v":[True,1,None]}}}
    trace={"manifest":manifest,"initialize":init,"steps":[accept,completed],"finish":True}
    def save(identity,t,features):
        code=trace_error(t)
        add("provider."+identity,"provider_trace",t,{"error_code":code} if code else {"accept":True},["provider."+f for f in features],"provider","providers/lifecycle",("transition",))
    save("completed",trace,["lifecycle","invocation"])
    for state in ("ERROR","CANCELLED","DEADLINE_EXCEEDED"):
        t=deepcopy(trace); o=t["steps"][-1]["outcome"]; o.pop("output"); o["state"]=state
        if state == "ERROR": o["error"]={"code":"com.example.failed","message":"deliberate"}
        if state == "CANCELLED": t["steps"].insert(1,{"action":"cancel","request":{"invocation_id":"attempt-1","reason":"golden"}})
        if state == "DEADLINE_EXCEEDED":
            t["steps"][0]["invocation"]["deadline"]="2026-01-01T00:00:00.0000000001Z"
            t["steps"][0]["now"]="2026-01-01T00:00:00Z"; t["steps"][-1]["now"]="2026-01-01T00:00:00.0000000001Z"
        save("outcome."+state,t,["lifecycle","cancellation" if state == "CANCELLED" else "deadlines" if state == "DEADLINE_EXCEEDED" else "faults"])
    for flags in itertools.product((False,True),repeat=4):
        for kind,payload in [("progress",None),("diagnostic",{}),("evidence",{"structured_data":[]}),("artifact",EXTERNAL),("resource_usage",USAGE),("extension",{"namespace":"com.example.event","data":[False,0]})]:
            t=deepcopy(trace); t["manifest"]["capabilities"][0]["lifecycle_features"]=dict(zip(lifecycle,flags))
            t["steps"].insert(1,{"action":"event","event":{"invocation_id":"attempt-1","sequence":1,"kind":kind,"payload":payload}})
            save("event."+''.join(str(int(x)) for x in flags)+"."+kind,t,["events"])
    for seq in ([1],[1,3],[2],[1,1],[1,0],[1,2,1],[True],[9007199254740992],[1.0]):
        t=deepcopy(trace)
        t["steps"][1:1]=[{"action":"event","event":{"invocation_id":"attempt-1","sequence":s,"kind":"progress","payload":None}} for s in seq]
        save("sequence."+str(len(INPUTS['providers/lifecycle'])),t,["events","correlation"])
    changes=[("duplicate_outcome",lambda t:t["steps"].append(deepcopy(completed)),["lifecycle"]),
        ("missing_outcome",lambda t:t["steps"].pop(),["lifecycle"]),
        ("running_prefix",lambda t:(t["steps"].pop(),t.update(finish=False)),["lifecycle"]),
        ("duplicate_invocation",lambda t:t["steps"].insert(1,deepcopy(accept)),["invocation"]),
        ("wrong_correlation",lambda t:t["steps"][-1]["outcome"].update(invocation_id="other"),["correlation"]),
        ("missing_capability",lambda t:t["steps"][0]["invocation"].update(capability_id="com.example.absent"),["invocation"]),
        ("wrong_version",lambda t:t["steps"][0]["invocation"].update(capability_version="2"),["invocation"]),
        ("wrong_contract",lambda t:t["initialize"].update(supported_contract_versions=["1.0"]),["negotiation"]),
        ("duplicate_capability",lambda t:t["manifest"]["capabilities"].append(deepcopy(cap)),["manifests"]),
        ("unknown_cancel",lambda t:t["steps"].insert(0,{"action":"cancel","request":{"invocation_id":"unknown"}}),["cancellation"]),
        ("cancel_after_terminal",lambda t:t["steps"].append({"action":"cancel","request":{"invocation_id":"attempt-1"}}),["cancellation"]),
        ("unsolicited_cancelled",lambda t:t["steps"][-1].update(outcome={"invocation_id":"attempt-1","state":"CANCELLED"}),["cancellation"]),
        ("invalid_input",lambda t:t["manifest"]["capabilities"][0].update(input_schema=False),["invocation"]),
        ("invalid_config",lambda t:t["manifest"]["capabilities"][0].update(config_schema=False),["invocation"]),
        ("invalid_output",lambda t:t["manifest"]["capabilities"][0].update(output_schema=False),["faults"])]
    for identity,fn,features in changes:
        t=deepcopy(trace); fn(t); save(identity,t,features)
    for at in ("2026-01-01T00:00:00Z","2026-01-01T00:00:00.00000000009Z","2026-01-01T00:00:00.0000000001Z","2026-01-01T00:00:00.00000000011Z"):
        for outcome in ("COMPLETED","DEADLINE_EXCEEDED"):
            t=deepcopy(trace); t["steps"][0]["invocation"]["deadline"]="2026-01-01T00:00:00.0000000001Z"; t["steps"][0]["now"]="2026-01-01T00:00:00Z"
            t["steps"][-1]["now"]=at
            if outcome != "COMPLETED": t["steps"][-1]["outcome"]={"invocation_id":"attempt-1","state":outcome}
            save("deadline."+str(len(INPUTS['providers/lifecycle'])),t,["deadlines"])
    for raw in [encode_frame({"unicode":"é😀"}),encode_frame({"a":1})+encode_frame({"b":2}),b"Content-Length: 0\r\n\r\n",b"Content-Length: 9\n\n{}",b"Content-Length: 5\r\nContent-Length: 5\r\n\r\n{}",b"Content-Length: 5\r\n\r\n{}"]:
        from tools.golden.provider_oracle import decode_frames
        try: expected={"messages":decode_frames(raw)}
        except ValueError: expected={"error_code":"PROTOCOL_VIOLATION"}
        add("provider.frame."+str(len(INPUTS['providers/framing'])),"provider_frame",{"hex":raw.hex()},expected,["provider.framing"],"provider","providers/framing",("boundary",))
    return manifest


def runtime_contract_cases():
    # These are declarative experiment instructions. The adapter must implement
    # the actual experiment; unsupported adapter operations fail, never pass.
    experiments = {
        "concurrency": ("ready_overlap", "dependency_barrier", "completion_order", "control_barrier", "shared_provider_serial"),
        "isolation": ("distinct_inputs", "distinct_bindings", "cancel_one_run", "separate_worktrees"),
        "cancellation": ("before_dispatch", "during_invocation", "near_completion", "after_terminal", "task_cancel"),
        "timeout": ("delayed_provider", "ignores_cancel_stdio"),
        "binding": ("no_match", "unique", "ambiguous", "explicit_correct", "explicit_incompatible", "provider_version", "capability_version", "identity_substitution"),
        "security": ("untrusted_command", "outside_root", "symlink_escape", "argv_no_shell"),
    }
    rules={"ready_overlap":"both providers enter before either is released", "dependency_barrier":"successor has not entered at predecessor barrier", "completion_order":"semantic records identical under reversed release order", "control_barrier":"Control executes without other active work", "shared_provider_serial":"default provider invocations do not overlap", "distinct_inputs":"no input or result crosses runs", "distinct_bindings":"each record identifies its configured provider", "cancel_one_run":"only addressed run cancels", "separate_worktrees":"candidate paths and content remain run-local", "before_dispatch":"CANCELLED without provider invocation", "during_invocation":"CANCELLED with no accepted output", "near_completion":"cancellation observed before acceptance discards output", "after_terminal":"terminal record remains unchanged", "task_cancel":"CancelledError and no fabricated record", "delayed_provider":"ERROR, never FAIL", "ignores_cancel_stdio":"process terminated, no successful accepted output", "no_match":"error before invocation", "unique":"one exact provider invoked", "ambiguous":"explicit binding required", "explicit_correct":"chosen exact binding recorded", "explicit_incompatible":"reject before invocation", "provider_version":"exact version required", "capability_version":"no version fallback", "identity_substitution":"reject mismatched trusted manifest", "untrusted_command":"graph cannot authorize executable", "outside_root":"unauthorized path rejected", "symlink_escape":"resolved path outside root rejected", "argv_no_shell":"metacharacters remain literal argv"}
    for topic,variants in experiments.items():
        for variant in variants:
            add("runtime."+topic+"."+variant,"runtime_experiment",{"experiment":topic,"variant":variant},{"invariant":rules[variant]},["relay."+topic],"relay-local","relay/"+topic,("interaction",))
    for name in ("ProviderCatalog","ProviderBinder","ExecutionDriver","ProviderTransport","RecordStore","EventObserver"):
        for variant in ("default","replacement","valid","invalid","exception","isolation"):
            expected="semantic contracts remain enforced"
            if name == "EventObserver" and variant == "exception": expected="observer failure recorded; verdict unchanged"
            if name == "RecordStore" and variant == "exception": expected="store error propagates to host"
            feats=["port."+name]
            if variant == "exception" and name in ("EventObserver","RecordStore"):
                feats.append("relay.observer_failure" if name == "EventObserver" else "relay.store_failure")
            add("port."+name+"."+variant,"port_experiment",{"port":name,"variant":variant},{"invariant":expected},feats,"relay-local","relay/extension-ports",("interaction",))
    for mutation in ("run_identity","subject","definition_identity","selected_subject","admission","node_identity","disposition","provider_id","capability_id","provider_version","capability_version","input_binding","input_source","consumed_value","producer_output","upstream_snapshot","guard","route","aggregate_members","weights","final_result","timing","cancellation"):
        exp={"error_code":"PROVENANCE_LINEAGE","single_contradiction":True}
        if mutation in ("run_identity","definition_identity","weights"):
            exp={"blocked_by_spec":"No portable authenticated run identity/hash or promise to rerun provider/reducer computation; a consistent identity/config rewrite alone is not a lineage contradiction","mutation":mutation}
        add("provenance.mutation."+mutation,"provenance_experiment",{"mutation":mutation},exp,["provenance"],"relay-local","vcp/provenance",("interaction",))
    for mutation in ("metadata","independent_overlap","optional_null"):
        add("provenance.allowed."+mutation,"provenance_experiment",{"mutation":mutation},{"accept":True},["provenance"],"relay-local","vcp/provenance")
    for name in ("pass_as_fail","unknown_as_pass","stale_output","ignored_guard","wrong_provider","schema_bypass","swapped_weights","ignored_stop","fabricated_usage","missing_provenance","provider_substitution","cancel_as_success","cross_run_leak"):
        add("mutant."+name,"mutation_probe",{"mutant":name},{"must_detect":True},["provenance","json.types"],"vcp","mutation/probes")


def integration_cases():
    variants={"read_text":["utf8","missing","binary","oversized"],"read_file":["binary","bounded"],"select_files":["files","glob","directory"],"git_scope":["WORKTREE","STAGED","UNSTAGED","untracked","rename","deleted"],"candidate_unchanged":["fresh","content_changed","head_changed"],"ruff":["violation","corrected"],"pytest":["pass","fail","collection_error"],"astgrep":["violation","corrected"],"scope":["files","changed_files","directory","changed_spans","ast_ranges","zero_deletion","half_open_boundary"],"no_findings":["empty","nonempty"],"text":["pass","fail","unicode_offsets","missing","terms_combine"],"json_parse":["valid","duplicate","nonfinite","malformed"],"schema":["valid","invalid","bool_number"],"action_policy":["allowed","denied","traversal","absolute"],"gate":["PASS","FAIL","UNKNOWN","ERROR","SKIP","DEFERRED","CANCELLED","NOT_APPLICABLE","KNOWN"],"command":["argv","stdout_stderr","nonzero","missing_executable","bounded_output","descendant_cleanup"],"command_check":["pass","fail"],"aggregate":["ALL"]}
    for capability,items in variants.items():
        for variant in items:
            optional="git" if capability in ("git_scope","candidate_unchanged") else "ruff" if capability == "ruff" else "ast-grep" if capability == "astgrep" else "pytest" if capability == "pytest" else None
            add("standard."+capability+"."+variant,"standard_experiment",{"capability":capability,"variant":variant,"external_tool":optional},{"contract_reference":"docs/relay/providers.md#"+capability},["standard."+capability],"integration","integrations/standard-providers",("boundary",))
    for entry,variants in {"python":["json","model","sync","builder"],"cli":["pass_stdin","fail_stdin","invalid_input","graph_stdin","both_stdin_reject","error_exit","unknown_exit"],"mcp":["tools","list","describe","run_pass","run_fail","inspect","unauthorized"],"http":["health","pass","fail","bad_token","oversized","unknown_graph"],"guardrail":["PASS","FAIL","UNKNOWN","ERROR","SKIP","DEFERRED","CANCELLED","NOT_APPLICABLE","KNOWN"],"multi_agent":["two_graphs","worktrees"]}.items():
        for variant in variants:
            add("integration."+entry+"."+variant,"integration_experiment",{"entrypoint":entry,"variant":variant},{"contract_reference":"docs/relay/integration.md","same_vcp_semantics":True},["integration."+entry],"integration","integrations/"+entry,("interaction",))


def build():
    if (BASE / "manifest.json").exists():
        raise SystemExit("immutable release already exists; author a new version, never update goldens")
    register_features()
    result_counts=result_cases(); wire_cases(); definition_cases(); graph_counts=graph_cases(); reducer_counts=reducer_cases()
    input_cases(); control_policy_cases(); comprehensive_cases(); manifest=provider_cases(); runtime_contract_cases(); integration_cases()
    for name in ("numeric_portability","sampling_identity","parallel_cancellation_provenance","transport_policy_provenance","authenticity"):
        add("blocked."+name,"blocked",{"question":name},{"blocked_by_spec":name},["open."+name],category="blocked/specification")
    for category,data in INPUTS.items(): write(BASE/"fixtures"/(category+".json"),data)
    for category,data in EXPECTED.items(): write(BASE/"expected"/(category+".json"),data)
    BASE.mkdir(parents=True,exist_ok=True)
    (BASE/"cases.jsonl").write_text(''.join(json.dumps(c,ensure_ascii=False,separators=(",",":"))+"\n" for c in CASES),encoding="utf-8",newline="\n")
    source_paths=sorted([*ROOT.glob("spec/draft/*.md"),*ROOT.glob("schemas/draft/*.json"),*ROOT.glob("provider-contract/spec/draft/*.md"),*ROOT.glob("provider-contract/schemas/draft/*.json"),*ROOT.glob("profiles/standard-draft/*"),*ROOT.glob("docs/relay/*.md"),ROOT/"README.md"])
    snapshot={"revision":REVISION,"sources":{p.relative_to(ROOT).as_posix():digest(p) for p in source_paths if p.is_file()},"authority_order":["normative prose semantics","normative schema structure","published local profile documentation"],"implementation_source_consulted_for_oracles":False,"relay_executed":False}
    write(BASE/"specification-snapshot.json",snapshot)
    write(BASE/"feature-matrix.json",list(FEATURES.values()))
    coverage={"unique_cases":len(CASES),"executed_cases":0,"execution_stage":"NOT_RUN_STAGE_A","result_enumeration":result_counts,"graph_enumeration":graph_counts,"reducer_enumeration":reducer_counts,"categories":dict(Counter(c["category"] for c in CASES)),"profiles":dict(Counter(c["profile"] for c in CASES)),"features":{k:{"valid":len(v["valid_case_ids"]),"invalid":len(v["invalid_case_ids"]),"boundary":len(v["boundary_case_ids"]),"interaction":len(v["interaction_case_ids"]),"transitions":len(v["transition_case_ids"]),"uncovered_obligations":[]} for k,v in FEATURES.items()},"finite_scope_complete":False,"reason":"Adapter and audit execution are separate stages; experiment declarations require operational verification. See coverage.md for exact limits."}
    write(BASE/"coverage.json",coverage)
    def source_set(prefix):
        items={k:v for k,v in snapshot["sources"].items() if k.startswith(prefix)}
        return hashlib.sha256(json.dumps(items,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    release={"suite_id":"openverify-golden-current","suite_version":RELEASE,"status":"DRAFT_SUITE_FROZEN_EXPECTATIONS","vcp":{"marker":"draft","specification_revision":REVISION,"specification_sha256":source_set("spec/draft/")},"provider_contract":{"marker":"0.1","status":"DRAFT","specification_revision":REVISION,"specification_sha256":source_set("provider-contract/spec/draft/")},"relay_profile":{"id":"relay-local","version":"0.1","runtime_revision":REVISION},"supported_feature_set":list(FEATURES),"required_tools":["Python 3.13","jsonschema","pytest","installed OpenVerify checkout for SUT invocation only"],"optional_tools":["git","ruff","ast-grep","mcp","starlette","httpx"],"case_count":len(CASES),"category_counts":coverage["categories"],"creation_commit":REVISION,"creation_commit_meaning":"clean parent revision before the expectation freeze commit; Git identifies freeze commit externally to avoid a self-reference","supersedes":None,"historical_suite":"unchanged; no inherited expectations or stale classifications","expectations_from_relay":False,"fixture_hashes":{},"oracle_source_hashes":{},"release_policy":"new suite version and preserved baseline required for any correction"}
    for p in sorted((BASE/"fixtures").rglob("*.json")): release["fixture_hashes"][p.relative_to(ROOT).as_posix()]=digest(p)
    for name in ("oracle.py","provider_oracle.py","compare.py","enumerate_graphs.py","enumerate_states.py","build_baseline.py","stdio_provider.py","verify_manifest.py"):
        p=ROOT/"tools/golden"/name; release["oracle_source_hashes"][p.relative_to(ROOT).as_posix()]=digest(p)
    write(BASE/"manifest.json",release)
    write(ROOT/"conformance/golden/manifest.json",{"suite_id":release["suite_id"],"current":BASE.relative_to(ROOT/"conformance/golden").as_posix(),"suite_version":RELEASE,"releases":[BASE.relative_to(ROOT/"conformance/golden").as_posix()]})
    checks={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(BASE.rglob("*")) if p.is_file() and p.name != "checksum-manifest.json"}
    checks.update(release["oracle_source_hashes"])
    write(BASE/"checksum-manifest.json",{"algorithm":"sha256","files":checks,"self_exclusion":"checksum-manifest.json is anchored by the Git freeze commit"})
    print(json.dumps({"cases":len(CASES),"result":result_counts,"graphs":graph_counts},indent=2))


if __name__ == "__main__":
    build()
