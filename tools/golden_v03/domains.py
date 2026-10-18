"""Compact bounded specification models. No SUT imports or execution."""
from copy import deepcopy
from itertools import product
import json

from tools.golden_v02.build_baseline import definition, edge, node, port, constant
from tools.golden_v02.enumerate_graphs import labeled_dags
from tools.golden_v02.oracle import EXCEPTIONAL, REDUCERS, result, reduce_results
from tools.golden_v03.expectations import DOMAIN, SUBJECT


def row(identity, operation, payload, expected, reference, category):
    return {"id": identity, "operation": operation, "input": payload, "expected": expected,
            "references": [reference], "feature_ids": [category], "category": category,
            "mutation_witness": "Invert the expected outcome or change one source/value/transition"}


def reducer_cases():
    for name in REDUCERS:
        base = [result("PASS", evidence=[{"message": "first"}]),
                result("FAIL", evidence=[{"message": "second"}])]
        if name in REDUCERS[3:7]:
            base = [result("KNOWN", score=0), result("KNOWN", score=1)]
        if name == "WORST_SEVERITY":
            base = [result("KNOWN", severity={"domain": DOMAIN["id"], "label": label})
                    for label in ("low", "high")]
        sequences = [[], [base[0]], base, base[::-1], [base[0], base[0]], [base[1], base[1]],
                     [base[0], base[1], base[0]]]
        sequences += [[base[0], result(e)] for e in EXCEPTIONAL if e != "MISSING"]
        sequences.append([base[0], result("KNOWN")])
        for i, seq in enumerate(sequences):
            for handling in ("IGNORE", "REJECT"):
                config = {"reducer": name, "handling": dict.fromkeys(EXCEPTIONAL, handling)}
                if name == "WEIGHTED_AVERAGE":
                    config["weights"] = [1] * len(seq)
                if name == "WORST_SEVERITY":
                    config["severity_domain"] = DOMAIN
                answer = reduce_results(name, seq, config)
                if i == 6 and name in ("AVERAGE", "WEIGHTED_AVERAGE"):
                    # Compare a mathematical interval, never invent a rounding rule.
                    answer = {"score_interval": [1 / 3 - 1e-15, 1 / 3 + 1e-15]}
                yield row(f"pure.reducer.{name}.{i}.{handling}", "reduce", {
                    "members": seq, "config": config}, answer,
                    "spec/draft/aggregation.md", "reducers")
    for name, members, weights in (
        ("retained_different_weights", [result("ERROR"), result("KNOWN", score=0),
                                       result("KNOWN", score=1)], [100, 1, 3]),
        ("zero", [result("KNOWN", score=1)], [0]),
        ("negative", [result("KNOWN", score=1)], [-1]),
        ("missing", [result("KNOWN", score=1)], []),
    ):
        config = {"reducer": "WEIGHTED_AVERAGE", "handling": dict.fromkeys(EXCEPTIONAL, "IGNORE"),
                  "weights": weights}
        yield row("pure.weighted." + name, "reduce", {"members": members, "config": config},
                  reduce_results("WEIGHTED_AVERAGE", members, config),
                  "spec/draft/aggregation.md", "reducers")
    for key in EXCEPTIONAL:
        for variant in ("missing", "invalid", "null", "wrong_type"):
            config = {"reducer": "ALL", "handling": dict.fromkeys(EXCEPTIONAL, "IGNORE")}
            if variant == "missing":
                del config["handling"][key]
            else:
                config["handling"][key] = {"invalid": "MAYBE", "null": None, "wrong_type": 1}[variant]
            yield row(f"pure.handling.{key}.{variant}", "reduce", {
                "members": [result("PASS")], "config": config}, {"error_code": "AGGREGATE_CONFIG"},
                "spec/draft/aggregation.md", "reducers")


def topology_cases():
    # 573 labeled DAGs, including the empty graph; no graph execution.
    for i, (n, pairs) in enumerate(labeled_dags(4)):
        yield row(f"dag.{i:03}", "parse_definition", definition(
            [node(str(k)) for k in range(n)], [edge(str(a), str(b)) for a, b in pairs]),
            {"accept": True}, "spec/draft/composition.md", "topology")
    shapes = {"single": (1, []), "independent": (2, []), "chain": (3, [(0, 1), (1, 2)]),
              "fanout": (3, [(0, 1), (0, 2)]), "fanin": (3, [(0, 2), (1, 2)]),
              "diamond": (4, [(0, 1), (0, 2), (1, 3), (2, 3)])}
    for shape, (n, pairs) in shapes.items():
        base = definition([node(str(k)) for k in range(n)], [edge(str(a), str(b)) for a, b in pairs])
        variants = [("self_loop", edge("0", "0"), "GRAPH_UNSUPPORTED"),
                    ("missing_source", edge("missing", "0"), "GRAPH_REFERENCE"),
                    ("missing_target", edge("0", "missing"), "GRAPH_REFERENCE")]
        if pairs:
            a, b = pairs[0]
            variants += [("duplicate_edge", edge(str(a), str(b)), "GRAPH_DUPLICATE"),
                         ("cycle", edge(str(b), str(a)), "GRAPH_UNSUPPORTED")]
        for name, addition, code in variants:
            d = deepcopy(base)
            d["graph"]["edges"].append(addition)
            yield row(f"mutation.{shape}.{name}", "parse_definition", d, {"error_code": code},
                      "spec/draft/composition.md", "topology")
        for name in ("duplicate_node", "wrong_kind", "expansion", "iteration", "delete_edge", "reverse_edge"):
            d = deepcopy(base)
            expected = {"accept": True}
            if name == "duplicate_node":
                d["graph"]["nodes"].append(deepcopy(d["graph"]["nodes"][0]))
                expected = {"error_code": "GRAPH_DUPLICATE"}
            elif name == "wrong_kind":
                d["graph"]["nodes"][0]["kind"] = "EXECUTE"
                expected = {"error_code": "PROTOCOL_STRUCTURE"}
            elif name in ("expansion", "iteration"):
                d["graph"]["features"] = ["DYNAMIC_EXPANSION" if name == "expansion" else "CYCLES"]
                expected = {"reject": True}  # unsupported feature spellings are schema-dependent
            elif pairs:
                first = d["graph"]["edges"].pop(0)
                if name == "reverse_edge":
                    d["graph"]["edges"].append(edge(first["to_node"], first["from_node"]))
            yield row(f"mutation.{shape}.{name}", "parse_definition", d, expected,
                      "spec/draft/composition.md", "topology")


def policy_cases():
    for role, values in (("activation", ["ACTIVATE", "DO_NOT_ACTIVATE"]),
                         ("admission", ["RUN", "SKIP", "DEFER"]),
                         ("selection", [[], [SUBJECT]])):
        field = "subjects" if role == "selection" else "outcome"
        for i, value in enumerate(values):
            yield row(f"policy.{role}.valid.{i}", "parse_object", {"object_type": role,
                "value": {field: value, "reason": "scripted"}}, {"accept": True},
                "spec/draft/execution-policy.md", "policies")
        for name, value in (("missing", {}), ("null", {field: None, "reason": "scripted"}),
                            ("enum", {field: "INVALID", "reason": "scripted"}),
                            ("empty_reason", {field: values[0], "reason": ""}),
                            ("wrong_type", {field: values[0], "reason": 1}),
                            ("conflict", {field: values[0], "reason": "x", "result": result("PASS")})):
            yield row(f"policy.{role}.{name}", "parse_object", {"object_type": role, "value": value},
                      {"error_code": "PROTOCOL_STRUCTURE"}, "spec/draft/execution-policy.md", "policies")
    yield row("policy.selection.duplicate", "parse_object", {"object_type": "selection",
        "value": {"subjects": [SUBJECT, SUBJECT], "reason": "x"}}, {"error_code": "POLICY_OUTPUT"},
        "spec/draft/execution-policy.md", "policies")


def availability_cases():
    """108 cells: six source/port profiles x six statuses x three handling rules.

    The historical 360-cell bound did not define its extra dimension. We do not
    pretend to reproduce it. Semantic Result ports expose bookkeeping Results.
    Invalid CONSTANT/EXTERNAL cells witness target-schema rejection at resolution;
    executable definitions reject these mismatches earlier (separate tests).
    """
    profiles = ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE", "UPSTREAM_INFORMATION",
                "UPSTREAM_RESULT", "UPSTREAM_DECISION")
    statuses = ("AVAILABLE", "ABSENT", "PRODUCER_NOT_EXECUTED", "PRODUCER_ERROR", "OUTPUT_MISSING", "INVALID")
    for profile, status, handling in product(profiles, statuses, ("BLOCK", "OMIT", "DEFAULT")):
        allowed = {"AVAILABLE", "INVALID"}
        if profile == "RUN_INPUT":
            allowed.add("ABSENT")
        if profile == "UPSTREAM_INFORMATION" or profile == "UPSTREAM_DECISION":
            allowed |= {"PRODUCER_NOT_EXECUTED", "PRODUCER_ERROR", "OUTPUT_MISSING"}
        payload = {"profile": profile, "status": status, "handling": handling}
        expected = {"applicable": status in allowed}
        if status not in allowed:
            expected["reason"] = ("Producer statuses apply only to upstream ports; ABSENT applies to run/unbound inputs; "
                                  "Result-role ports publish recorded error/nonexecution Results")
        else:
            expected.update(status=status, blocked=status != "AVAILABLE" and handling == "BLOCK",
                            used_default=status != "AVAILABLE" and handling == "DEFAULT",
                            omitted=status != "AVAILABLE" and handling == "OMIT")
        yield row(f"availability.{profile}.{status}.{handling}", "availability", payload, expected,
                  "spec/draft/dataflow.md", "availability")


def guard_cases():
    # Equality is the ONLY supported operator. JSON type equality is mandatory.
    for i, (actual, expected, enabled) in enumerate((
        (True, True, True), (True, 1, False), (False, 0, False), (None, None, True),
        ("x", "x", True), ("x", "y", False), ([1, False], [1, 0], False),
        ({"a": 1}, {"a": 1}, True), ({"a": 1}, {}, False), (0, 0.0, True))):
        yield row(f"guard.equality.{i}", "guard", {"actual": actual, "expected": expected,
            "pointer": ""}, {"enabled": enabled}, "spec/draft/dataflow.md", "guards")
    for name, pointer, value, enabled in (("nested", "/a/0", 1, True),
        ("missing", "/missing", None, False), ("escaped", "/a~1b/~0", 2, True)):
        yield row("guard.pointer." + name, "guard", {"actual": {"a": [1], "a/b": {"~": 2}},
            "expected": value, "pointer": pointer}, {"enabled": enabled},
            "spec/draft/dataflow.md", "guards")


def readiness_cases():
    for n in range(4):
        # Terminal subsets test scheduling; no provider or graph execution.
        for mask in range(1 << n):
            for control in range(-1, n):
                ids = [str(i) for i in range(n)]
                terminal = [x for i, x in enumerate(ids) if mask & (1 << i)]
                ready = [x for x in ids if x not in terminal]
                expected = []
                for identity in ready:
                    if int(identity) == control:
                        expected = expected or [identity]
                        break
                    expected.append(identity)
                yield row(f"readiness.{n}.{mask}.{control}", "readiness", {
                    "nodes": [node(x, "CONTROL" if int(x) == control else "DERIVE") for x in ids],
                    "terminal": terminal}, {"ready": expected},
                    "spec/draft/open-questions.md#relay-v01-implementation-boundaries-not-new-vcp-semantics",
                    "readiness")
