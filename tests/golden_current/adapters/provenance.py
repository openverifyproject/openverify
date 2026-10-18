"""One-relationship contradictions; the validator is the SUT, not the oracle."""

from __future__ import annotations

from copy import deepcopy

from tests.golden_current.adapters.public import run_scenario
from tools.golden.verify_manifest import resolve


async def experiment(payload):
    from openverify import parse_run_record

    sc = deepcopy(resolve("fixtures/relay/graphs.json#/comprehensive.PASS"))
    baseline = (await run_scenario(sc))["record"]
    # This confirms a real baseline was accepted, not that its execution is true.
    parse_run_record(baseline)
    record = deepcopy(baseline)
    nodes = {n["node_id"]: n for n in record["nodes"]}
    mutation = payload["mutation"]
    if mutation == "subject":
        record["subject"]["id"] = "other.subject"
    elif mutation == "selected_subject":
        record["policy_evaluations"][1]["outcome"]["subjects"][0]["id"] = "other.subject"
    elif mutation == "admission":
        record["admission"]["outcome"] = "DEFER"
    elif mutation == "node_identity":
        nodes["D1"]["node_id"] = "nonexistent"
    elif mutation == "disposition":
        nodes["E1"]["result"] = {"protocol": "draft", "disposition": "SKIPPED"}
    elif mutation in ("provider_id", "provider_version", "capability_id", "capability_version"):
        nodes["D1"]["provider_binding"][mutation] = (
            "com.example.substituted" if mutation.endswith("id") else "substituted"
        )
    elif mutation == "input_binding":
        record["definition"]["graph"]["nodes"][0]["bindings"]["constant"]["value"] = 4
    elif mutation == "input_source":
        nodes["D1"]["input_resolutions"]["constant"]["source"]["value"] = 4
    elif mutation == "consumed_value":
        nodes["D1"]["input_values"]["constant"] = 4
    elif mutation == "producer_output":
        nodes["D1"]["information"]["value"] = {"fabricated": True}
    elif mutation == "upstream_snapshot":
        nodes["A1"]["upstream_results"]["E1"]["verdict"] = "FAIL"
    elif mutation == "guard":
        record["definition"]["graph"]["edges"][0]["guard"] = {
            "source": {"kind": "CONSTANT", "value": False},
            "pointer": "",
            "value": True,
        }
    elif mutation == "route":
        nodes["C1"]["decision"]["destination"] = "E4"
    elif mutation == "aggregate_members":
        nodes["A1"]["input_values"]["members"].reverse()
    elif mutation == "final_result":
        record["final_results"]["E1"]["verdict"] = "FAIL"
    elif mutation == "timing":
        nodes["E1"]["started_at"] = "0001-01-01T00:00:00Z"
    elif mutation == "cancellation":
        record["cancellation"] = {
            "node_id": "D1",
            "phase": "BEFORE_START",
            "reason": "unobserved cancellation",
        }
    elif mutation == "metadata":
        record.setdefault("metadata", {})["benign"] = [False, 0, True, 1]
    elif mutation == "optional_null":
        nodes["D1"]["reason"] = None
    elif mutation == "independent_overlap":
        # D2 and E1 share D1 as predecessor and have no edge between them.
        start = max(nodes["D2"]["started_at"], nodes["E1"]["started_at"])
        finish = min(nodes["D2"]["finished_at"], nodes["E1"]["finished_at"])
        if finish < start:
            # Both can use the same zero-duration point within their shared
            # prerequisite/successor bounds; no wall-clock fabrication claim.
            start = min(nodes["D2"]["finished_at"], nodes["E1"]["finished_at"])
        for key in ("D2", "E1"):
            nodes[key]["started_at"] = start
            nodes[key]["finished_at"] = start
    else:
        raise ValueError("unrecognized frozen provenance mutation " + mutation)
    parse_run_record(record)
    return {"accept": True}
