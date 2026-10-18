"""Mutation of actual execution observations challenges the Golden checks.

This is observation mutation sensitivity, not production source mutation testing.
"""

from copy import deepcopy
from tools.golden_v02.compare import Difference
from tools.golden_v02.oracle import check_record
from tools.golden_v02.verify_manifest import resolve
from tests.golden_v02.adapters.public import run_scenario


async def probe(payload):
    name = payload["mutant"]
    reference = {
        "ignored_guard": "fixtures/vcp/graph-control.json#/guard.literal.False",
        "ignored_stop": "fixtures/vcp/graph-control.json#/control.graph.STOP_SUCCESS",
        "unknown_as_pass": "fixtures/relay/graphs.json#/comprehensive.UNKNOWN",
        "swapped_weights": "fixtures/relay/reducer-boundaries.json#/v02.graph.reducer.WEIGHTED_AVERAGE.valid",
    }.get(name, "fixtures/relay/graphs.json#/comprehensive.PASS")
    sc = deepcopy(resolve(reference))
    observed = await run_scenario(sc)
    sc["definition"] = observed["definition"]
    record = observed["record"]
    check_record(record, sc)
    corrupted = deepcopy(record)
    nodes = {n["node_id"]: n for n in corrupted["nodes"]}
    if name == "pass_as_fail":
        nodes["E1"]["result"]["verdict"] = "FAIL"
    elif name == "unknown_as_pass":
        nodes["E1"]["result"].update(determination="KNOWN", verdict="PASS")
    elif name == "stale_output":
        nodes["E1"]["input_values"]["data"] = "stale"
    elif name == "ignored_guard":
        nodes["c"]["state"] = "SUCCESS"
    elif name in ("wrong_provider", "provider_substitution"):
        nodes["D1"]["executor_ref"] = "com.example.wrong"
        nodes["D1"]["provider_binding"]["provider_id"] = "com.example.wrong"
        corrupted["provider_bindings"]["D1"]["provider_id"] = "com.example.wrong"
    elif name == "schema_bypass":
        nodes["D1"]["input_values"]["constant"] = True
    elif name == "swapped_weights":
        nodes["a"]["result"]["score"] = 0.25
        corrupted["final_results"]["a"]["score"] = 0.25
    elif name == "ignored_stop":
        nodes["a"]["state"] = "SUCCESS"
    elif name == "fabricated_usage":
        nodes["D1"]["usage"]["com.example.calls"]["value"] = 3
    elif name == "missing_provenance":
        del nodes["D1"]["input_resolutions"]["constant"]["source"]
    elif name == "cancel_as_success":
        nodes["D1"]["state"] = "CANCELLED"
    elif name == "cross_run_leak":
        corrupted["run_inputs"]["payload"] = {"different_run": True}
    elif name == "contradictory_availability":
        nodes["D1"]["input_resolutions"]["constant"]["status"] = "INVALID"
    else:
        raise AssertionError("unknown frozen mutation " + name)
    try:
        check_record(corrupted, sc)
    except Difference as exc:
        return {
            "detected": True,
            "mutant": name,
            "invariant": str(exc),
            "scope": "actual execution observation mutation",
        }
    return {"detected": False, "mutant": name}
