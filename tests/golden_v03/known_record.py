"""Pure record parsing plus external trusted fixture anchors; never executes Relay."""
from copy import deepcopy
import json
from tests.golden_v03.target import BASE
from tools.golden_v02.compare import equal


def check(mutation):
    from openverify import parse_run_record
    from openverify.errors import ProtocolError
    known = json.loads((BASE / "known-record.json").read_text(encoding="utf-8"))
    record = deepcopy(known)
    nodes = {n["node_id"]: n for n in record["nodes"]}
    if mutation == "provider_version":
        nodes["derive"]["executor_version"] = "forged"
        nodes["derive"]["provider_binding"]["provider_version"] = "forged"
        record["provider_bindings"]["derive"]["provider_version"] = "forged"
    elif mutation == "upstream_result":
        next(n for n in record["nodes"] if "judge" in n["upstream_results"])["upstream_results"]["judge"]["verdict"] = "FAIL"
    elif mutation == "criterion":
        nodes["judge"]["input_values"]["criterion"]["id"] = "forged"
    elif mutation == "input":
        nodes["judge"]["input_values"]["x"] = 99
    elif mutation == "output":
        nodes["derive"]["information"]["x"] = 99
    elif mutation == "run_id":
        record["run_id"] = "forged"
    elif mutation == "subject":
        record["subject"]["id"] = "forged"
    elif mutation == "node_occurrence":
        record["nodes"].append(deepcopy(record["nodes"][0]))
    elif mutation == "definition_id":
        record["definition"]["id"] = "forged"
    elif mutation == "usage":
        nodes["derive"]["usage"]["wall_time"]["value"] = -1
    elif mutation == "evidence":
        nodes["judge"]["result"]["evidence"] = [{"message": "forged evidence"}]
    elif mutation is not None:
        raise AssertionError("Unknown provenance mutation: " + mutation)
    try:
        parse_run_record(record)
    except ProtocolError as exc:
        assert mutation is not None, f"Known record rejected: {exc}"
        assert str(exc.code) in ("PROVENANCE_LINEAGE", "PROTOCOL_STRUCTURE", "SEMANTIC_BINDING")
        return
    # A coherent rewrite can remain SDK-valid. Known fixture/provider anchors
    # deliberately reject it, without asserting SDK external authentication.
    try:
        equal(known, record)
    except AssertionError:
        assert mutation is not None
        return
    assert mutation is None, "Corrupted record escaped both semantic and trusted-anchor checks"
