"""Additional spec-derived examples. No implementation imports or observations."""

from copy import deepcopy
from itertools import product


def build(b):
    for name, value in (("omitted", b.MISSING), ("null", None)):
        obj = {"protocol": "draft"}
        if value is not b.MISSING:
            obj["disposition"] = value
        b.add(
            "v02.result.disposition." + name,
            "parse_result",
            obj,
            {"error_code": "PROTOCOL_STRUCTURE"},
            ["result.axes"],
            "vcp",
            "vcp/result-boundaries",
            ("boundary",),
        )
    outcomes = {
        "ACTIVATION": {"outcome": "ACTIVATE", "reason": "known"},
        "SELECTION": {"subjects": [b.SUBJECT], "reason": "known"},
        "ADMISSION": {"outcome": "RUN", "reason": "known"},
    }
    for role, source in product(outcomes, ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE")):
        n = b.node("n")
        expected = {"n": b.success(n, {"value": 1})}
        value = b.EXTERNAL if source == "EXTERNAL_REFERENCE" else {"remaining": 0, "unit": "call"}
        binding = (
            b.constant(value)
            if source == "CONSTANT"
            else {"kind": "RUN_INPUT", "name": "budget"}
            if source == "RUN_INPUT"
            else {"kind": "EXTERNAL_REFERENCE", "reference": value}
        )
        sc = b.scenario(
            [n],
            [],
            {"n": b.behavior({"value": 1})},
            expected,
            {"budget": value} if source == "RUN_INPUT" else {},
            [b.port("budget")] if source == "RUN_INPUT" else [],
            policies={role: outcomes[role]},
        )
        policy = sc["definition"]["execution_policy"][role.lower()]
        policy["inputs"] = [b.port("budget", {"type": "object"})]
        policy["bindings"] = {"budget": binding}
        b.add(
            f"v02.policy.typed.{role}.{source}",
            "policy_run",
            sc,
            {"nodes": expected, "policy_input": value},
            ["policies", "policy." + role.lower(), "provenance"],
            "relay-local",
            "relay/typed-policies",
            ("interaction",),
        )
    for role in outcomes:
        for malformed in (
            {},
            {"outcome": "INVALID", "reason": "known"},
            {"outcome": "RUN", "reason": ""},
            {"result": b.result("PASS")},
        ):
            n = b.node("n")
            sc = b.scenario(
                [n], [], {"n": b.behavior({"value": 1})}, {}, policies={role: malformed}
            )
            index = len(b.INPUTS["relay/invalid-policies"])
            b.add(
                f"v02.policy.invalid.{role}.{index}",
                "policy_run",
                sc,
                {"error_code": "POLICY_OUTPUT", "occurrence": False},
                ["policies", "policy." + role.lower()],
                "relay-local",
                "relay/invalid-policies",
                ("boundary",),
            )
        n = b.node("n")
        sc = b.scenario(
            [n],
            [],
            {"n": b.behavior({"value": 1})},
            {},
            policies={role: outcomes[role]},
            policy_behaviors={
                role: {"error": {"code": "com.example.policy_failed", "message": "known failure"}}
            },
        )
        b.add(
            "v02.policy.failure." + role,
            "policy_run",
            sc,
            {"error_code": "POLICY_OUTPUT", "occurrence": False},
            ["policies", "policy." + role.lower()],
            "relay-local",
            "relay/invalid-policies",
            ("boundary",),
        )
    b.add(
        "v02.mutant.contradictory_availability",
        "mutation_probe",
        {"mutant": "contradictory_availability"},
        {"must_detect": True, "contract": "A consumed valid constant cannot be INVALID"},
        ["provenance", "availability.AVAILABLE"],
        "vcp",
        "mutation/probes",
        ("boundary",),
    )
    b.add(
        "v02.standard.read_text.utf8_crlf",
        "standard_experiment",
        {"capability": "read_text", "variant": "utf8_crlf", "external_tool": None},
        {"byte_contract": "UTF-8 retains CRLF exactly; size and SHA256 over bytes"},
        ["standard.read_text"],
        "integration",
        "integrations/byte-boundaries",
        ("boundary",),
    )
    for variant in ("directory_child", "sibling", "trailing_traversal", "backslash_traversal"):
        b.add(
            "v02.standard.action_policy." + variant,
            "standard_experiment",
            {"capability": "action_policy", "variant": variant, "external_tool": None},
            {
                "verdict": "PASS" if variant == "directory_child" else "FAIL",
                "prefix": "tmp/",
                "boundary": "Only directory children; traversal rejected",
            },
            ["standard.action_policy"],
            "integration",
            "integrations/path-boundaries",
            ("boundary",),
        )
    for mode in (
        "valid",
        "stderr",
        "failing",
        "crash",
        "malformed",
        "wrong_correlation",
        "missing_terminal",
        "duplicate",
        "event_after_terminal",
    ):
        b.add(
            "v02.provider.stdio." + mode,
            "stdio_experiment",
            {"mode": mode},
            {
                "state": "SUCCESS" if mode in ("valid", "stderr") else "ERROR",
                "information": {"value": "a"} if mode in ("valid", "stderr") else {},
                "contract": "Real initialized external peer; invalid messages/outcomes must not become accepted verification",
            },
            ["provider.framing", "provider.faults", "relay.binding"],
            "provider",
            "providers/stdio-sessions",
            ("interaction",),
        )
    base = deepcopy(b.INPUTS["providers/lifecycle"]["provider.completed"])
    for name, schema in (
        ("negative_minLength", {"minLength": -1}),
        ("nested_id", {"$defs": {"x": {"$id": "nested", "type": "string"}}}),
        ("annotation_id", {"default": {"$id": "ordinary-data"}}),
    ):
        trace = deepcopy(base)
        trace["manifest"]["capabilities"][0]["input_schema"] = schema
        b.add(
            "v02.provider.schema." + name,
            "provider_trace",
            trace,
            {"accept": True}
            if name == "annotation_id"
            else {"error_code": "INVALID_PROVIDER_OUTPUT"},
            ["provider.manifests"],
            "provider",
            "providers/schema-regressions",
            ("boundary",),
        )
    for year, precision, position in product(
        ("0001", "2026", "9999"), (20, 80), ("before", "equal", "after")
    ):
        trace = deepcopy(base)
        prefix = year + "-01-01T00:00:00"
        trace["steps"][0]["invocation"]["deadline"] = prefix + "." + "0" * precision + "2Z"
        trace["steps"][0]["now"] = prefix + "Z"
        trace["steps"][-1]["now"] = (
            prefix
            + "."
            + "0" * precision
            + {"before": "1", "equal": "2", "after": "3"}[position]
            + "Z"
        )
        for terminal in ("COMPLETED", "DEADLINE_EXCEEDED"):
            t = deepcopy(trace)
            t["steps"][-1]["outcome"] = {
                "invocation_id": "attempt-1",
                "state": terminal,
                **({"output": {"v": [True, 1, None]}} if terminal == "COMPLETED" else {}),
            }
            valid = (position == "before") == (terminal == "COMPLETED")
            b.add(
                f"v02.provider.deadline.{year}.{precision}.{position}.{terminal}",
                "provider_trace",
                t,
                {"accept": True} if valid else {"error_code": "PROTOCOL_VIOLATION"},
                ["provider.deadlines"],
                "provider",
                "providers/deadline-regressions",
                ("boundary",),
            )
    reserved = "CONTRACT_VERSION_UNSUPPORTED CAPABILITY_UNAVAILABLE CAPABILITY_VERSION_UNSUPPORTED INVALID_INVOCATION INVALID_CONFIG INVALID_INPUT INVALID_PROVIDER_OUTPUT PROTOCOL_VIOLATION".split()
    for code in reserved + ["com.example.failed", "AGGREGATE_INPUT", "ERROR", "foo.failed"]:
        obj = {
            "invocation_id": "attempt-1",
            "state": "ERROR",
            "error": {
                "code": code,
                "message": "informative",
                "details": {"identity": [False, 0, None]},
            },
        }
        valid = code in reserved or code == "com.example.failed"
        b.add(
            "v02.provider.error_code." + code,
            "provider_object",
            {"object_type": "outcome", "value": obj},
            {"accept": True, "preserve": obj}
            if valid
            else {"error_code": "INVALID_PROVIDER_OUTPUT"},
            ["provider.faults"],
            "provider",
            "providers/error-vocabulary",
            ("boundary",),
        )
    # Separate graph boundary for every reducer, including reordered membership.
    for reducer in b.REDUCERS:
        for variant in ("valid", "reverse_edges", "provider_error", "wrong_output", "custom"):
            numeric = reducer in ("MIN_SCORE", "MAX_SCORE", "AVERAGE", "WEIGHTED_AVERAGE")
            severity = reducer == "WORST_SEVERITY"
            domain = {
                "id": "golden.domain",
                "levels": [{"label": "low", "rank": 1}, {"label": "high", "rank": 2}],
            }
            values = [
                b.result("KNOWN", score=v)
                if numeric
                else b.result("KNOWN", severity={"domain": "golden.domain", "label": label})
                if severity
                else b.result(label)
                for v, label in (
                    (0, "low" if severity else "PASS"),
                    (1, "high" if severity else "PASS"),
                )
            ]
            p, q = b.node("p", "EVALUATE"), b.node("q", "EVALUATE")
            config = {"reducer": reducer, "handling": dict.fromkeys(b.EXCEPTIONAL, "REJECT")}
            if numeric and reducer == "WEIGHTED_AVERAGE":
                config["weights"] = {"left": 1, "right": 3}
            if severity:
                config["severity_domain"] = domain
            a = b.node(
                "a",
                "AGGREGATE",
                [b.port("left"), b.port("right"), b.port("members")],
                {
                    "left": b.upstream("p", "result"),
                    "right": b.upstream("q", "result"),
                    "members": b.constant(["left", "right"]),
                },
                capability="com.example.golden.custom"
                if variant == "custom"
                else "openverify.aggregate",
                config=config,
            )
            a["aggregate_inputs"] = ["left", "right"]
            calc_config = deepcopy(config)
            if "weights" in calc_config:
                calc_config["weights"] = [1, 3]
            computed = b.reduce_results(reducer, values, calc_config)["result"]
            behaviors = {
                "p": b.behavior({"result": values[0]}),
                "q": b.behavior({"result": values[1]}),
            }
            expected = {
                "p": b.success(p, {"result": values[0]}),
                "q": b.success(q, {"result": values[1]}),
                "a": b.success(a, {"result": computed}),
            }
            if variant in ("custom", "wrong_output", "provider_error"):
                behaviors["a"] = b.behavior({"result": computed})
            if variant == "provider_error":
                behaviors["a"] = b.behavior(
                    error={"code": "com.example.failed", "message": "known failure"}
                )
            elif variant == "wrong_output":
                behaviors["a"] = b.behavior({"result": b.result("SKIP")})
            if variant in ("provider_error", "wrong_output"):
                expected["a"] = {"state": "ERROR", "information": {}, "result": b.result("ERROR")}
            edges = [("p", "a"), ("q", "a")]
            if variant == "reverse_edges":
                edges.reverse()
            sc = b.scenario([p, q, a], edges, behaviors, expected)
            b.add(
                f"v02.graph.reducer.{reducer}.{variant}",
                "run",
                sc,
                {"nodes": expected},
                ["reducer." + reducer, "node.AGGREGATE", "aggregate.membership"],
                "relay-local",
                "relay/reducer-boundaries",
                ("interaction",),
            )

    # All node kinds and unavailable handling for actual nonexecuted producers.
    for kind, mode, availability in product(
        b.KINDS,
        ("BLOCK", "OMIT", "DEFAULT"),
        (
            "ABSENT",
            "PRODUCER_ERROR",
            "PRODUCER_NOT_EXECUTED",
            "OUTPUT_MISSING",
            "INVALID",
            "AVAILABLE",
        ),
    ):
        target = b.port(
            "data", required=mode == "BLOCK", default=0 if mode == "DEFAULT" else b.MISSING
        )
        binding = (
            {"data": {"kind": "RUN_INPUT", "name": "data"}}
            if availability == "ABSENT"
            else {"data": b.upstream("p")}
        )
        p = b.node("p")
        inputs = [target]
        if kind == "AGGREGATE":
            p = b.node("p", "EVALUATE")
            # Aggregate members must be required BLOCK RESULTs: other handling
            # applies to a separate ordinary semantic information input.
            inputs += [b.port("member"), b.port("members")]
            binding["member"] = b.upstream("p", "result")
            binding["members"] = b.constant(["member"])
            if availability != "ABSENT":
                p["outputs"].append({"name": "value", "schema": True, "role": "INFORMATION"})
        n = b.node("n", kind, inputs, binding)
        if kind == "AGGREGATE":
            n["aggregate_inputs"] = ["member"]
        pout = (
            {"result": b.result("PASS"), "value": False}
            if kind == "AGGREGATE" and availability != "ABSENT"
            else {"result": b.result("PASS")}
            if kind == "AGGREGATE"
            else {"value": False}
        )
        nout = (
            {"value": False}
            if kind == "DERIVE"
            else {"decision": {"protocol": "draft", "kind": "CONTINUE"}}
            if kind == "CONTROL"
            else {"result": b.result("PASS")}
        )
        pb = b.behavior(pout)
        pe = b.success(p, pout)
        nodes, edges = [p, n], [("p", "n")]
        if availability == "PRODUCER_ERROR":
            pb = b.behavior(error={"code": "com.example.failed", "message": "known failure"})
            pe = {"state": "ERROR", "information": {}, "result": b.result("ERROR")}
        if availability in ("OUTPUT_MISSING", "INVALID"):
            if availability == "OUTPUT_MISSING":
                pb = b.behavior({"result": b.result("PASS")} if kind == "AGGREGATE" else {})
            else:
                next(o for o in p["outputs"] if o["name"] == "value")["schema"] = {"type": "string"}
            pe = {"state": "ERROR", "information": {}, "result": b.result("ERROR")}
        if availability == "PRODUCER_NOT_EXECUTED":
            anchor = b.node("anchor")
            nodes.insert(0, anchor)
            edges.insert(
                0,
                b.edge("anchor", "p", {"source": b.constant(False), "pointer": "", "value": True}),
            )
            pe = b.nonexecution("GUARD_FALSE")
        ne = (
            b.nonexecution("INPUT_UNAVAILABLE")
            if availability != "AVAILABLE" and mode == "BLOCK"
            else b.success(n, nout)
        )
        expectations = {"p": pe, "n": ne}
        behaviors = {"p": pb, "n": b.behavior(nout)}
        if availability == "PRODUCER_NOT_EXECUTED":
            expectations["anchor"] = b.success(anchor, {"value": "anchor"})
            behaviors["anchor"] = b.behavior({"value": "anchor"})
        sc = b.scenario(
            nodes,
            edges,
            behaviors,
            expectations,
            declarations=[b.port("data", required=False)] if availability == "ABSENT" else [],
        )
        b.add(
            f"v02.availability.{kind}.{availability}.{mode}",
            "run",
            sc,
            {"nodes": expectations},
            ["node." + kind, "availability." + availability, "provenance"],
            "relay-local",
            "relay/availability-matrix",
            ("interaction",),
        )

    # A partial usage observation of 3 is superseded by final usage of 7.
    for kind in b.KINDS:
        n = b.node("n", kind)
        nodes = [n]
        edges = []
        out = (
            {"value": 1}
            if kind == "DERIVE"
            else {"decision": {"protocol": "draft", "kind": "CONTINUE"}}
            if kind == "CONTROL"
            else {"result": b.result("PASS")}
        )
        expectations = {"n": b.success(n, out)}
        behaviors = {}
        if kind == "AGGREGATE":
            p = b.node("p", "EVALUATE")
            n["inputs"] += [b.port("member"), b.port("members")]
            n["bindings"].update(member=b.upstream("p", "result"), members=b.constant(["member"]))
            n["aggregate_inputs"] = ["member"]
            nodes.insert(0, p)
            edges = [("p", "n")]
            behaviors["p"] = b.behavior({"result": b.result("PASS")})
            expectations["p"] = b.success(p, {"result": b.result("PASS")})
        partial = {"com.example.calls": {"kind": "EXACT", "unit": "call", "value": 3}}
        final = {"com.example.calls": {"kind": "EXACT", "unit": "call", "value": 7}}
        behaviors["n"] = b.behavior(
            out, events=[{"kind": "resource_usage", "payload": partial}], usage=final
        )
        sc = b.scenario(nodes, edges, behaviors, expectations)
        b.add(
            "v02.usage.final_authority." + kind,
            "run",
            sc,
            {"nodes": expectations, "authoritative_usage": final, "partial_usage": partial},
            ["resources", "provenance", "node." + kind],
            "relay-local",
            "relay/resource-authority",
            ("boundary",),
        )
