"""Pure and real-Relay adapters for each frozen availability cell."""
from copy import deepcopy
import json
from time import perf_counter_ns
from tools.golden_v02.compare import equal
from tools.golden_v02.oracle import result
from tests.golden_v031.structure_adapter import wire


def consumer_values(case):
    s, expected = case["stimulus"], case["stimulus"]["expected"]
    consumer = next(n for n in s["definition"]["graph"]["nodes"] if n["id"] == "consumer")
    values = {}
    for name, source in consumer["bindings"].items():
        if name == "data":
            continue
        if source["kind"] == "CONSTANT":
            values[name] = deepcopy(source["value"])
        else:
            values[name] = deepcopy(s["behaviors"][source["node_id"]]["outputs"][source["output"]])
    if expected["has_value"]:
        values["data"] = deepcopy(expected["value"])
    return values


def assert_resolution(case, resolution, values, blocked):
    expected = case["stimulus"]["expected"]
    equal(expected["status"], resolution["status"])
    equal(expected["source"], resolution.get("source"))
    equal(expected["used_default"], resolution["used_default"])
    equal(expected["has_value"], "value" in resolution)
    if expected["has_value"]:
        equal(expected["value"], resolution["value"])
    equal(consumer_values(case), values)
    equal(expected["blocked"], blocked)


def mutation_witness(case, resolution, values, blocked):
    corrupted = deepcopy(resolution)
    corrupted["status"] = "INVALID" if resolution["status"] != "INVALID" else "AVAILABLE"
    try:
        assert_resolution(case, corrupted, values, blocked)
    except AssertionError:
        return
    raise AssertionError(case["id"] + ": status mutant survived")


def pure(case):
    if not case["runtime_applicable"]:
        assert case["reason"]
        if case.get("static_rejection"):
            from openverify import parse_definition
            from openverify.errors import ProtocolError
            try:
                parse_definition(case["stimulus"]["definition"])
            except ProtocolError as exc:
                equal(case["static_rejection"], str(exc.code))
            else:
                raise AssertionError("Illegal optional Aggregate RESULT member accepted")
        return
    from openverify import parse_definition
    from openverify.dataflow import resolve_inputs
    from openverify.model import NodeRecord
    s = case["stimulus"]
    d = parse_definition(s["definition"])
    records = {}
    for n in s["definition"]["graph"]["nodes"]:
        if n["id"] == "consumer":
            continue
        b = s["behaviors"][n["id"]]
        record = {"node_id": n["id"], "kind": n["kind"], "operation": n["operation"],
            "upstream_node_ids": [], "upstream_results": {}, "input_values": {}, "input_resolutions": {},
            "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:00Z",
            "usage": {}, "state": "SUCCESS", "information": {}}
        if n["id"] == "producer" and case["availability"] == "PRODUCER_NOT_EXECUTED":
            record.update(state="NONEXECUTED", reason="GUARD_FALSE", result=result("SKIP"))
        elif "error" in b:
            record.update(state="ERROR", result=result("ERROR"), observation={"outputs": {}, "error": b["error"]})
        elif n["id"] == "producer" and case["availability"] in ("OUTPUT_MISSING", "INVALID"):
            record.update(state="ERROR", reason="OUTPUT_MISSING" if case["availability"] == "OUTPUT_MISSING" else "OUTPUT_INVALID",
                          result=result("ERROR"), observation={"outputs": b["outputs"]})
        else:
            record["observation"] = {"outputs": b["outputs"]}
            for p in n["outputs"]:
                if p["role"] == "INFORMATION":
                    record["information"][p["name"]] = b["outputs"][p["name"]]
                else:
                    record[p["name"]] = b["outputs"][p["name"]]
        records[n["id"]] = NodeRecord.model_validate(record)
    run_values = deepcopy(s["inputs"])
    consumer = next(n for n in d.graph.nodes if n.id == "consumer")
    values, resolutions, blocked = resolve_inputs(consumer, run_values, records, d.graph)
    actual = wire(resolutions["data"])
    assert_resolution(case, actual, values, blocked)
    mutation_witness(case, actual, values, blocked)


class Transport:
    def __init__(self, identity, behavior, calls):
        self.identity, self.behavior, self.calls = identity, deepcopy(behavior), calls

    async def invoke(self, request, emit):
        from openverify.provider import Outcome, ProviderError
        inv = request.invocation
        self.calls.append({"node": self.identity, "input": deepcopy(inv.input), "config": deepcopy(inv.config),
                           "invocation_id": inv.invocation_id})
        b = self.behavior
        if "error" in b:
            return Outcome(invocation_id=inv.invocation_id, state="ERROR", error=ProviderError(**b["error"]))
        return Outcome(invocation_id=inv.invocation_id, state="COMPLETED", output=deepcopy(b["outputs"]))


async def runtime(case, report):
    from openverify import Relay, parse_definition, parse_run_record
    from openverify.relay.adapters.catalog import Catalog
    from openverify.relay import RuntimeConfig
    from openverify.model import ProviderBinding
    from tests.golden_v02.adapters.public import manifest_for
    s, calls = case["stimulus"], []
    definition = parse_definition(s["definition"])
    catalog, bindings = Catalog(), {}
    for n in s["definition"]["graph"]["nodes"]:
        manifest = manifest_for(n["id"], n["operation"])
        catalog.register_transport(manifest, Transport(n["id"], s["behaviors"][n["id"]], calls))
        bindings[n["id"]] = ProviderBinding(provider_id=manifest.provider_id, provider_version="1", **n["operation"])
    start = perf_counter_ns()
    report.relay_calls["MASTER EXECUTION"] += 1
    try:
        run = await Relay(catalog=catalog, config=RuntimeConfig(bindings=bindings)).run(definition, inputs=deepcopy(s["inputs"]), opportunity_id=case["id"])
    finally:
        report.relay_ns["MASTER EXECUTION"] += perf_counter_ns() - start
    record = json.loads(run.to_json())
    parse_run_record(run.to_json())
    nodes = {n["node_id"]: n for n in record["nodes"]}
    equal(sorted(n["id"] for n in s["definition"]["graph"]["nodes"]), sorted(nodes))
    equal(s["inputs"], record["run_inputs"])
    equal(case["id"], record["opportunity_id"])
    consumer, expected = nodes["consumer"], s["expected"]
    assert_resolution(case, consumer["input_resolutions"]["data"], consumer["input_values"], consumer["state"] == "NONEXECUTED")
    invoked = [c for c in calls if c["node"] == "consumer"]
    equal(1 if expected["consumer_invoked"] else 0, len(invoked))
    if expected["consumer_invoked"]:
        equal("SUCCESS", consumer["state"])
        equal(consumer_values(case), invoked[0]["input"])
        equal(expected["consumer_outputs"], consumer["observation"]["outputs"])
        if case["node_kind"] == "DERIVE":
            equal(expected["consumer_outputs"], consumer["information"])
        else:
            field = "decision" if case["node_kind"] == "CONTROL" else "result"
            equal(expected["consumer_outputs"][field], consumer[field])
    else:
        equal("INPUT_UNAVAILABLE", consumer["reason"])
        equal("SKIPPED", consumer["result"]["disposition"])
        equal({"reason": "INPUT_UNAVAILABLE"}, consumer["result"]["output"])
        equal({}, consumer["usage"])
        assert consumer.get("provider_binding") is None and consumer.get("observation") is None
    for identity, n in nodes.items():
        if n.get("provider_binding"):
            equal("com.example.golden.p_" + identity, n["provider_binding"]["provider_id"])
            equal("1", n["provider_binding"]["provider_version"])
            equal(n["provider_binding"], record["provider_bindings"][identity])
        for producer, snapshot in n["upstream_results"].items():
            equal(nodes[producer]["result"], snapshot)
        for name, resolution in n["input_resolutions"].items():
            if "value" in resolution:
                equal(resolution["value"], n["input_values"][name])
    if case["source"] == "UPSTREAM_OUTPUT":
        p = nodes["producer"]
        if case["availability"] == "PRODUCER_NOT_EXECUTED":
            equal("NONEXECUTED", p["state"])
            equal("GUARD_FALSE", p["reason"])
            assert not [c for c in calls if c["node"] == "producer"]
        elif case["availability"] in ("PRODUCER_ERROR", "OUTPUT_MISSING", "INVALID"):
            equal("ERROR", p["state"])
            equal({}, p["information"])
        else:
            equal("SUCCESS", p["state"])
    mutation_witness(case, consumer["input_resolutions"]["data"], consumer["input_values"], expected["blocked"])
