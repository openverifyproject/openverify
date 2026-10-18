"""Only public parsers and independently callable pure functions; never Relay.run."""
from copy import deepcopy
import json

from tools.golden_v02.compare import equal
from tools.golden_v02.oracle import normalized_result


def wire(value):
    from openverify import serialize
    return json.loads(serialize(value))


def invoke(case):
    from openverify import parse_definition, parse_result, flattened_status
    from openverify.validation import parse_object
    from openverify.provider import parse_provider_object, validate_lifecycle, wire_data
    p, op = deepcopy(case["input"]), case["operation"]
    if op == "parse_result":
        value = parse_result(p)
        from openverify.errors import ProtocolError
        try:
            projection = flattened_status(value)
        except ProtocolError as exc:
            assert exc.code == "RESULT_PROJECTION"
            projection = None
        return {"value": wire(value), "projection": projection}
    if op == "parse_definition":
        return {"value": wire(parse_definition(p))}
    if op in ("parse_object", "parse_raw"):
        return {"value": wire(parse_object(p["object_type"], p.get("raw", p.get("value"))))}
    if op == "provider_object":
        return {"value": wire_data(parse_provider_object(p["object_type"], p["value"]))}
    if op == "provider_trace":
        validate_lifecycle(p)
        return {"accept": True}
    if op == "reduce":
        from openverify.relay.core.aggregation import reduce_results
        names = [f"m{i}" for i in range(len(p["members"]))]
        config = p["config"]
        if "weights" in config:
            # Bad count must be rejected before dict construction loses a member.
            from openverify.validation import aggregate_config
            aggregate_config(config, len(names))
            config["weights"] = dict(zip(names, config["weights"]))
        inputs = {"members": names, **dict(zip(names, p["members"]))}
        return {"result": wire(reduce_results(inputs, config))}
    if op == "availability":
        return availability(p)
    if op == "guard":
        from openverify.dataflow import guards_enabled
        from tools.golden_v02.build_baseline import definition, edge, node
        from openverify.model import Graph
        d = definition([node("a"), node("b")], [edge("a", "b", {
            "source": {"kind": "RUN_INPUT", "name": "x"}, "pointer": p["pointer"], "value": p["expected"]})])
        return {"enabled": guards_enabled("b", Graph.model_validate(d["graph"]), {"x": p["actual"]}, {})}
    if op == "readiness":
        from openverify.model import Graph
        from openverify.relay.core.readiness import ready_wave
        graph = Graph.model_validate({"nodes": p["nodes"], "edges": []})
        return {"ready": [n.id for n in ready_wave(graph, set(p["terminal"]), 8)]}
    if op == "dependency_readiness":
        from openverify.model import Graph
        from openverify.relay.core.readiness import ready_wave
        return {"ready": [n.id for n in ready_wave(Graph.model_validate(p["graph"]), set(p["terminal"]), 8)]}
    if op == "compatibility":
        from openverify.model import OperationRequirement
        from openverify.provider import ProviderManifest
        from openverify.relay.ports import AvailableProvider
        from openverify.relay.ports.binding import compatible
        from tests.golden_v02.adapters.public import manifest_for
        requirement = {"capability_id": "com.example.golden.derive", "capability_version": "1"}
        manifest = wire_data(manifest_for("pure", requirement))
        for key, value in p.items():
            if key.startswith("supported_"):
                manifest[key] = value
                if key == "supported_vcp_versions":
                    manifest["capabilities"][0].pop("vcp_version")
            else:
                manifest["capabilities"][0][key] = value
        return {"compatible": compatible(OperationRequirement(**requirement),
                AvailableProvider(ProviderManifest.model_validate(manifest), None))}
    if op == "policy_outcome":
        from openverify.policy import check_outcome
        from tools.golden_v02.build_baseline import definition, node
        d = parse_definition(definition([node("n")]))
        check_outcome(p["role"], parse_object(p["object_type"], p["value"]), d)
        return {"accept": True}
    if op == "guard_source":
        return guard_source(p)
    raise AssertionError("Unimplemented pure adapter: " + op)


def availability(p):
    from openverify.dataflow import resolve_inputs
    from openverify.model import Graph, Node, NodeRecord
    from tools.golden_v02.build_baseline import node, port, upstream, constant, EXTERNAL
    from tools.golden_v02.oracle import result
    profile, status, handling = p["profile"], p["status"], p["handling"]
    role = "RESULT" if profile.endswith("RESULT") else "DECISION" if profile.endswith("DECISION") else "INFORMATION"
    value = result("PASS", evidence=[], usage={}) if role == "RESULT" else {"protocol": "draft", "kind": "CONTINUE"} if role == "DECISION" else 5
    source = constant(value)
    run_values, records = {}, {}
    output = role.lower() if role != "INFORMATION" else "value"
    producer = node("producer", "EVALUATE" if role == "RESULT" else "CONTROL" if role == "DECISION" else "DERIVE")
    if profile == "RUN_INPUT":
        source = {"kind": "RUN_INPUT", "name": "x"}
        if status != "ABSENT":
            run_values["x"] = value
    elif profile == "EXTERNAL_REFERENCE":
        source, value = {"kind": "EXTERNAL_REFERENCE", "reference": EXTERNAL}, EXTERNAL
    elif profile.startswith("UPSTREAM"):
        source = upstream("producer", output)
        record = {"node_id": "producer", "kind": producer["kind"], "operation": producer["operation"],
            "upstream_node_ids": [], "upstream_results": {}, "input_values": {}, "input_resolutions": {},
            "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:00Z",
            "usage": {}, "state": "SUCCESS", "information": {}}
        if status in ("AVAILABLE", "INVALID"):
            if role == "INFORMATION":
                record["information"][output] = value
            else:
                record[output] = value
        elif status == "PRODUCER_NOT_EXECUTED":
            record.update(state="NONEXECUTED", result=result("SKIP"), reason="GUARD_FALSE")
        elif status == "PRODUCER_ERROR":
            record.update(state="ERROR", result=result("ERROR"))
        elif status == "OUTPUT_MISSING":
            record.update(state="ERROR", result=result("ERROR"), reason="OUTPUT_MISSING")
        records["producer"] = NodeRecord.model_validate(record)
    target_schema = False if status == "INVALID" else True
    # DEFAULT must be schema-valid even when source is invalid.
    if status == "INVALID":
        target_schema = {"const": "fallback"}
    target = port("x", target_schema, handling == "BLOCK")
    target["on_unavailable"] = handling
    if handling == "DEFAULT":
        target["default"] = constant("fallback")
    consumer = Node.model_validate(node("consumer", inputs=[target], bindings={"x": source}))
    graph = Graph.model_validate({"nodes": [producer, wire(consumer)], "edges": [{"from_node": "producer", "to_node": "consumer"}]})
    values, resolutions, blocked = resolve_inputs(consumer, run_values, records, graph)
    resolution = wire(resolutions["x"])
    expected_value = "fallback" if status != "AVAILABLE" and handling == "DEFAULT" else value
    if status == "AVAILABLE" or handling == "DEFAULT":
        equal({"x": expected_value}, values)
        equal(expected_value, resolution["value"])
    else:
        equal({}, values)
        assert "value" not in resolution
    return {"status": resolution["status"], "used_default": resolution["used_default"],
            "blocked": blocked, "omitted": "x" not in values and handling == "OMIT" and status != "AVAILABLE"}


def check(case):
    from openverify.errors import ProtocolError
    from openverify.provider import ProviderContractError
    expected = case["expected"]
    if case["operation"] == "availability031":
        from tests.golden_v031.availability_adapter import pure
        pure(case["input"])
        return
    if case["operation"] == "phase":
        from openverify.relay.core.state import RunState
        initial, target = case["input"]["initial"], case["input"]["target"]
        state = RunState({"n": initial})
        try:
            state.transition("n", target)
        except ValueError:
            assert not expected["allowed"]
            equal(initial, state.phases["n"])
        else:
            assert expected["allowed"]
            equal(target, state.phases["n"])
        return
    if case["operation"] == "known_record":
        from tests.golden_v031.known_record import check as check_record
        check_record(case["input"]["mutation"])
        return
    if expected.get("applicable") is False:
        assert expected.get("reason"), "Inapplicable cell must explain why"
        return
    try:
        observed = invoke(case)
    except (ProtocolError, ProviderContractError) as exc:
        assert expected.get("error_code") or expected.get("reject"), f"Unexpected {exc.code}: {exc}"
        if expected.get("error_code"):
            equal(expected["error_code"], str(exc.code))
        if expected.get("allowed_error_codes"):
            assert str(exc.code) in expected["allowed_error_codes"], exc
        return
    assert not (expected.get("error_code") or expected.get("reject")), "Expected rejection; accepted"
    if "preserve" in expected:
        if case["operation"] == "parse_result":
            equal(normalized_result(expected["preserve"]), normalized_result(observed["value"]))
            equal(expected["projection"], observed["projection"])
        else:
            equal(expected["preserve"], observed["value"])
    if case["operation"] == "reduce":
        if "score_interval" in expected:
            low, high = expected["score_interval"]
            assert low <= observed["result"]["score"] <= high
        else:
            equal(normalized_result(expected["result"]), normalized_result(observed["result"]))
    if case["operation"] in ("availability", "guard", "guard_source", "readiness", "dependency_readiness", "compatibility"):
        equal({k: v for k, v in expected.items() if k != "applicable"}, observed)


def guard_source(p):
    from openverify.dataflow import guards_enabled
    from openverify.model import Graph, NodeRecord
    from tools.golden_v02.build_baseline import node, edge, constant, upstream, EXTERNAL
    from tools.golden_v02.oracle import result
    profile, unavailable = p["profile"], p["unavailable"]
    kind = "EVALUATE" if profile == "UPSTREAM_RESULT" else "CONTROL" if profile == "UPSTREAM_DECISION" else "DERIVE"
    producer = node("producer", kind)
    records, run_values = {}, {}
    source, pointer, literal = constant(True), "", bool(p["matches"])
    if profile == "RUN_INPUT":
        source = {"kind": "RUN_INPUT", "name": "x"}
        if not unavailable:
            run_values["x"] = True
    elif profile == "EXTERNAL_REFERENCE":
        source, pointer = {"kind": "EXTERNAL_REFERENCE", "reference": EXTERNAL}, "/id"
        literal = EXTERNAL["id"] if p["matches"] else "different"
    elif profile.startswith("UPSTREAM"):
        output = "result" if kind == "EVALUATE" else "decision" if kind == "CONTROL" else "value"
        source = upstream("producer", output)
        record = {"node_id": "producer", "kind": kind, "operation": producer["operation"],
            "upstream_node_ids": [], "upstream_results": {}, "input_values": {}, "input_resolutions": {},
            "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:00Z",
            "usage": {}, "state": "SUCCESS", "information": {}}
        if kind == "EVALUATE":
            record["result"] = result("UNKNOWN" if unavailable else "PASS")
            pointer, literal = "/verdict", "PASS" if p["matches"] else "FAIL"
        elif kind == "CONTROL":
            pointer, literal = "/kind", "CONTINUE" if p["matches"] else "STOP_SUCCESS"
            if not unavailable:
                record["decision"] = {"protocol": "draft", "kind": "CONTINUE"}
        elif not unavailable:
            record["information"]["value"] = True
        if unavailable and kind != "EVALUATE":
            record.update(state="NONEXECUTED", result=result("SKIP"), reason="GUARD_FALSE")
        records["producer"] = NodeRecord.model_validate(record)
    graph = Graph.model_validate({"nodes": [producer, node("consumer")], "edges": [edge(
        "producer", "consumer", {"source": source, "pointer": pointer, "value": literal})]})
    return {"enabled": guards_enabled("consumer", graph, run_values, records)}
