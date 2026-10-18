"""Independent trusted-script record audit; no SUT imports.

Checks consistency and known script anchors, not coherent external forgery.
"""
from copy import deepcopy
from fractions import Fraction
from tools.golden_v02.compare import equal, fields, utc
from tools.golden_v02.oracle import MISSING, normalized_result
from tools.golden_v03.expectations import USAGE


def authored_fields(expected, observed, path=""):
    """Every authored field survives; SDK materialized defaults may be additional."""
    if isinstance(expected, dict):
        assert isinstance(observed, dict), path
        for key, value in expected.items():
            assert key in observed, path + "/" + key
            authored_fields(value, observed[key], path + "/" + key)
    elif isinstance(expected, list):
        assert isinstance(observed, list) and len(expected) == len(observed), path
        for i, (a, b) in enumerate(zip(expected, observed)):
            authored_fields(a, b, path + "/" + str(i))
    else:
        equal(expected, observed, path)


def result_equal(expected, actual):
    if expected.get("execution_outcome") == "SUCCESS":
        wanted, observed = normalized_result(expected), normalized_result(actual)
        if "score" in wanted:
            # Numerical portability is open. A tight interval tests the math law,
            # without requiring any cross-language bitwise rounding convention.
            target = Fraction(wanted.pop("score"))
            score = observed.pop("score")
            assert not isinstance(score, bool) and isinstance(score, (int, float))
            assert abs(Fraction(score) - target) <= Fraction(1, 10**14), (score, target)
        equal(wanted, observed)
    else:
        fields(expected, actual)
        for key in ("applicability", "determination", "judgment", "verdict", "score", "severity"):
            assert actual.get(key) is None, (key, actual)


def audit(record, scenario, calls):
    d = scenario["definition"]
    authored_fields(d, record["definition"])
    assert isinstance(record["run_id"], str) and record["run_id"]
    equal(d["id"], record["definition"]["id"])
    equal(d["version"], record["definition"]["version"])
    equal(d["subject"], record["subject"])
    equal(d["criterion"], record["definition"]["criterion"])
    equal(scenario["inputs"], record["run_inputs"])
    by_id = {n["node_id"]: n for n in record["nodes"]}
    authored = {n["id"]: n for n in d["graph"]["nodes"]}
    equal(list(authored), [n["node_id"] for n in record["nodes"]])
    assert len(by_id) == len(authored)
    begin, end = utc(record["started_at"]), utc(record["finished_at"])
    assert begin <= end
    run_values = deepcopy(scenario["inputs"])
    for p in d["run_inputs"]:
        if p["name"] not in run_values and p["on_unavailable"] == "DEFAULT":
            run_values[p["name"]] = p["default"]["value"]
    expected_invoked = []
    equal(sorted(k for k, v in scenario["nodes"].items() if "result" in v),
          sorted(record["final_results"]))
    for identity, spec in authored.items():
        n, expected = by_id[identity], scenario["nodes"][identity]
        fields({k: v for k, v in expected.items() if k not in ("result", "absent")}, n, identity)
        fields({"kind": spec["kind"], "operation": spec["operation"]}, n, identity)
        assert begin <= utc(n["started_at"]) <= utc(n["finished_at"]) <= end
        if "result" in expected:
            result_equal(expected["result"], n["result"])
        predecessors = [e["from_node"] for e in d["graph"]["edges"] if e["to_node"] == identity]
        equal(predecessors, n["upstream_node_ids"])
        for predecessor in predecessors:
            assert utc(by_id[predecessor]["finished_at"]) <= utc(n["started_at"])
        upstream = {k: by_id[k]["result"] for k in predecessors if by_id[k].get("result") is not None}
        equal(upstream, n["upstream_results"], identity + "/upstream_results")
        values = {}
        equal(sorted(p["name"] for p in spec["inputs"]), sorted(n["input_resolutions"]))
        for p in spec["inputs"]:
            name, source = p["name"], spec["bindings"].get(p["name"])
            resolution = n["input_resolutions"][name]
            equal(source, resolution.get("source"), identity + "/" + name + "/source")
            value, status = MISSING, "ABSENT"
            if source is not None:
                kind = source["kind"]
                if kind == "CONSTANT":
                    value = source["value"]
                elif kind == "EXTERNAL_REFERENCE":
                    value = source["reference"]
                elif kind == "RUN_INPUT":
                    value = run_values.get(source["name"], MISSING)
                else:
                    producer_id, output = source["node_id"], source["output"]
                    facts = scenario["nodes"][producer_id]
                    if output == "result" and "result" in facts:
                        # Audit producer against independent facts, then require
                        # byte/JSON-exact repeated snapshots, including diagnostics.
                        value = by_id[producer_id]["result"]
                    elif output == "decision":
                        value = facts.get("decision", MISSING)
                    else:
                        value = facts.get("information", {}).get(output, MISSING)
                    if value is MISSING:
                        if facts["state"] in ("NONEXECUTED", "CANCELLED"):
                            status = "PRODUCER_NOT_EXECUTED"
                        elif facts["state"] == "ERROR":
                            b = scenario["behaviors"].get(producer_id, {})
                            if b.get("error") or b.get("raise") or b.get("hang") or b.get("duplicate_terminal") or b.get("invalid_event"):
                                status = "PRODUCER_ERROR"
                            elif output not in b.get("outputs", {}):
                                status = "OUTPUT_MISSING"
                            else:
                                status = "INVALID"
                        else:
                            status = "OUTPUT_MISSING"
            if value is not MISSING:
                status = "AVAILABLE"
            equal(status, resolution["status"], identity + "/" + name + "/status")
            default = status != "AVAILABLE" and p["on_unavailable"] == "DEFAULT"
            equal(default, resolution["used_default"])
            if default:
                value = p["default"]["value"]
            if value is not MISSING:
                equal(value, resolution["value"], identity + "/" + name + "/value")
                values[name] = value
            else:
                assert "value" not in resolution
        equal(values, n["input_values"], identity + "/input_values")
        if spec["kind"] in ("EVALUATE", "AGGREGATE"):
            equal(d["subject"], values["subject"])
            equal(d["criterion"], values["criterion"])
        if expected["state"] == "NONEXECUTED":
            assert not n["usage"] and not n["information"]
            for key in ("observation", "provider_binding", "executor_ref", "executor_version", "decision"):
                assert n.get(key) is None, (identity, key)
            assert identity not in record.get("provider_bindings", {})
        else:
            binding = n["provider_binding"]
            equal(binding, record["provider_bindings"][identity])
            # Scripted manifests are trusted external anchors for this harness.
            if identity in scenario["behaviors"]:
                provider = "com.example.golden.p_" + identity.lower()
                equal(provider, binding["provider_id"])
                equal("1", binding["provider_version"])
                equal(provider, n["executor_ref"])
                equal("1", n["executor_version"])
                expected_invoked.append(provider)
                invoked = [c for c in calls if c["provider_id"] == provider]
                assert len(invoked) == 1, (identity, invoked)
                equal(values, invoked[0]["input"])
                equal(spec["config"], invoked[0]["config"])
                if expected["state"] == "SUCCESS":
                    equal(scenario["behaviors"][identity]["outputs"], n["observation"]["outputs"])
                if scenario["behaviors"][identity].get("usage"):
                    fields(USAGE, n["usage"])
                    equal(USAGE, n["observation"]["usage"])
            fields(spec["operation"], binding)
            assert n["usage"]["wall_time"]["value"] >= 0
            equal("s", n["usage"]["wall_time"]["unit"])
            equal("EXACT", n["usage"]["wall_time"]["kind"])
        if n.get("result") is not None:
            equal(n["result"], record["final_results"][identity])
    equal(sorted(expected_invoked), sorted(c["provider_id"] for c in calls if ".p_policy_" not in c["provider_id"]))
    equal(["ACTIVATION", "SELECTION", "ADMISSION"], [p["role"] for p in record["policy_evaluations"]])
    for p in record["policy_evaluations"]:
        role = p["role"]
        equal(scenario["policies"][role], p["outcome"])
        equal({"choice": run_values[role.lower()]}, p["input_values"])
        equal("com.example.golden.p_policy_" + role.lower(), p["executor_ref"])
        equal("1", p["executor_version"])
        invoked = [c for c in calls if c["provider_id"] == p["executor_ref"]]
        assert len(invoked) == 1, (role, invoked)
        equal({"choice": run_values[role.lower()]}, invoked[0]["input"])
        equal({}, invoked[0]["config"])
    equal(scenario["policies"]["ADMISSION"], record["admission"])


def corruptions(record):
    """One invariant at a time, including all three historical oracle weaknesses."""
    for name in ("known_provider_version", "upstream_result", "embedded_criterion",
                 "consumed_value", "source_identity", "exact_output", "evidence", "resources",
                 "node_occurrence", "definition_identity", "run_identity", "final_result"):
        r = deepcopy(record)
        nodes = {n["node_id"]: n for n in r["nodes"]}
        if name == "known_provider_version":
            # Coherent change beats internal consistency, but fails trusted manifest.
            nodes["D1"]["executor_version"] = "forged"
            nodes["D1"]["provider_binding"]["provider_version"] = "forged"
            r["provider_bindings"]["D1"]["provider_version"] = "forged"
        elif name == "upstream_result":
            nodes["A_ALL"]["upstream_results"]["E1"]["verdict"] = "FAIL"
        elif name == "embedded_criterion":
            nodes["E1"]["input_values"]["criterion"]["id"] = "forged"
        elif name == "consumed_value":
            nodes["E2"]["input_values"]["data"] = 99
        elif name == "source_identity":
            nodes["E2"]["input_resolutions"]["data"]["source"]["node_id"] = "D2"
        elif name == "exact_output":
            nodes["D1"]["information"]["value"] = 99
        elif name == "evidence":
            nodes["A_ALL"]["result"]["evidence"] = []
        elif name == "resources":
            nodes["D1"]["usage"]["wall_time"]["value"] = -1
        elif name == "node_occurrence":
            r["nodes"].append(deepcopy(r["nodes"][0]))
        elif name == "definition_identity":
            r["definition"]["id"] = "forged"
        elif name == "run_identity":
            r["run_id"] = ""
        elif name == "final_result":
            r["final_results"]["E1"]["verdict"] = "FAIL"
        yield name, r
