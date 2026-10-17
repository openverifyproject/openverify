"""Spec-derived stimuli, separate from all execution adapters. No SUT imports.

Authorities: spec/draft/{dataflow,result,wire-format,lifecycle,provenance}.md;
provider-contract/spec/draft/{lifecycle,errors}.md; docs/relay/architecture.md.
"""
from copy import deepcopy
from itertools import product
from tools.golden_v02.build_baseline import definition, node, port, constant, edge, upstream
from tools.golden_v02.oracle import result, MISSING

KINDS = ("DERIVE", "EVALUATE", "AGGREGATE", "CONTROL")
SOURCES = ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE", "UPSTREAM_OUTPUT", "UNBOUND")
STATES = ("AVAILABLE", "ABSENT", "PRODUCER_NOT_EXECUTED", "PRODUCER_ERROR", "OUTPUT_MISSING", "INVALID")
HANDLING = ("BLOCK", "OMIT", "DEFAULT")
PASS = result("PASS", evidence=[], usage={})
DECISION = {"protocol": "draft", "kind": "CONTINUE"}
EXTERNAL = {"id": "golden.external", "type": "application/json", "locator": {"opaque": "never-fetch"}}


def applicable(source, state, handling, role="INFORMATION"):
    if source in ("CONSTANT", "EXTERNAL_REFERENCE"):
        return state == "AVAILABLE", "Authored constants/references resolve AVAILABLE; invalid known values reject definitions before execution"
    if source == "RUN_INPUT":
        return state in ("AVAILABLE", "ABSENT", "INVALID"), "Run inputs can be supplied, omitted, or fail the consuming port's schema; they have no producer"
    if source == "UNBOUND":
        return state == "ABSENT" and handling != "BLOCK", "Only optional inputs may be unbound; required BLOCK without a binding rejects the definition"
    if role == "RESULT":
        return state in ("AVAILABLE", "INVALID"), "Recorded evaluator Results, including error/nonexecution bookkeeping, are available unless excluded by a declared port schema"
    return state != "ABSENT", "Upstream outputs have a declared producer; unpublished information/Decisions classify by producer state, not ABSENT"


def output(kind, value=7):
    return {"value": value} if kind == "DERIVE" else {"decision": DECISION} if kind == "CONTROL" else {"result": PASS}


def build_availability(kind, source, state, handling, role="INFORMATION"):
    """Authored valid graph, exact scripted behavior and independent resolution."""
    inputs, declarations, behaviors, nodes, edges = {}, [], {}, [], []
    target = port("data", {"type": "integer", "minimum": 0}, handling == "BLOCK",
                  0 if handling == "DEFAULT" else MISSING)
    value = 7
    if source == "EXTERNAL_REFERENCE":
        target["schema"] = {"type": "object"}
        if handling == "DEFAULT":
            target["default"] = constant({"fallback": True})
        binding, value = {"kind": "EXTERNAL_REFERENCE", "reference": EXTERNAL}, EXTERNAL
    elif source == "CONSTANT":
        binding = constant(value)
    elif source == "RUN_INPUT":
        binding = {"kind": "RUN_INPUT", "name": "payload"}
        declarations = [port("payload", True, False)]
        if state != "ABSENT":
            inputs["payload"] = -1 if state == "INVALID" else value
    elif source == "UNBOUND":
        binding = None
    else:
        producer_kind = "EVALUATE" if role == "RESULT" else "CONTROL" if role == "DECISION" else "DERIVE"
        p = node("producer", producer_kind)
        if role == "INFORMATION":
            p["outputs"][0]["schema"] = {"type": "integer"}
        produced = output(producer_kind)
        value = PASS if role == "RESULT" else DECISION if role == "DECISION" else 7
        target["schema"] = True if role != "INFORMATION" else target["schema"]
        if state == "INVALID" and role == "RESULT":
            p["outputs"][0]["schema"] = {"type": "object", "properties": {"execution_outcome": {"const": "SUCCESS"}}}
        output_name = "result" if role == "RESULT" else "decision" if role == "DECISION" else "value"
        binding = upstream("producer", output_name)
        b = {"outputs": produced}
        if state == "PRODUCER_ERROR" or (state == "INVALID" and role == "RESULT"):
            b = {"error": {"code": "com.example.scripted_failure", "message": "known producer failure"}}
        elif state == "OUTPUT_MISSING":
            b = {"outputs": {}}
        elif state == "INVALID":
            b = {"outputs": {"decision": {"protocol": "draft", "kind": "INVALID"}}} if role == "DECISION" else {"outputs": {"value": "invalid"}}
        elif state == "PRODUCER_NOT_EXECUTED":
            anchor = node("anchor")
            nodes.append(anchor)
            behaviors["anchor"] = {"outputs": {"value": 1}}
            edges.append(edge("anchor", "producer", {"source": constant(False), "pointer": "", "value": True}))
        nodes.append(p)
        behaviors["producer"] = b
        edges.append(edge("producer", "consumer"))
    ports, bindings = [target], {} if binding is None else {"data": binding}
    if kind == "AGGREGATE":
        member = node("member", "EVALUATE")
        nodes.append(member)
        behaviors["member"] = {"outputs": {"result": PASS}}
        edges.append(edge("member", "consumer"))
        ports += [port("member"), port("members")]
        bindings.update(member=upstream("member", "result"), members=constant(["member"]))
    consumer = node("consumer", kind, ports, bindings,
                    capability="com.example.golden.custom_aggregate" if kind == "AGGREGATE" else None)
    if kind == "AGGREGATE":
        consumer["aggregate_inputs"] = ["member"]
    nodes.append(consumer)
    behaviors["consumer"] = {"outputs": output(kind)}
    usable = state == "AVAILABLE" or handling == "DEFAULT"
    consumed = value if state == "AVAILABLE" else target.get("default", {}).get("value")
    expected = {"status": state, "used_default": state != "AVAILABLE" and handling == "DEFAULT",
        "has_value": usable, "blocked": state != "AVAILABLE" and handling == "BLOCK",
        "consumer_invoked": not (state != "AVAILABLE" and handling == "BLOCK"),
        "source": binding, "consumer_outputs": output(kind)}
    if usable:
        expected["value"] = consumed
    return {"definition": definition(nodes, edges, declarations), "inputs": inputs,
            "behaviors": behaviors, "expected": expected}


def availability_cases():
    for kind, source, state, handling in product(KINDS, SOURCES, STATES, HANDLING):
        active, why = applicable(source, state, handling)
        case = {"id": f"availability360.{kind}.{source}.{state}.{handling}", "node_kind": kind,
            "source": source, "availability": state, "handling": handling, "role": "INFORMATION",
            "runtime_applicable": active, "reason": why, "category": "availability360",
            "requirement": "spec/draft/dataflow.md#typed-executable-dataflow-breaking-draft-revision",
            "mutation_witness": "Change consumed value/source/status/default flag, invoke a blocked consumer, or invent a Result verdict"}
        if active:
            case["stimulus"] = build_availability(kind, source, state, handling)
        yield case


def role_cases():
    for role, kind, state, handling in product(("RESULT", "DECISION"), KINDS, STATES, HANDLING):
        active, why = applicable("UPSTREAM_OUTPUT", state, handling, role)
        c = {"id": f"availability-role.{role}.{kind}.{state}.{handling}", "node_kind": kind,
            "source": "UPSTREAM_OUTPUT", "availability": state, "handling": handling, "role": role,
            "runtime_applicable": active, "reason": why, "category": "availability-role",
            "requirement": "spec/draft/dataflow.md#typed-executable-dataflow-breaking-draft-revision",
            "mutation_witness": "Confuse information with semantic output roles or leak invalid/unpublished values"}
        if active:
            c["stimulus"] = build_availability(kind, "UPSTREAM_OUTPUT", state, handling, role)
        yield c


PORTS = {
    "Catalog": {"methods": {"providers": "() -> Sequence[AvailableProvider]"},
        "contract": "Trusted provider snapshot; validate manifests, unique identities, sequence shape; no work before successful binding"},
    "Binder": {"methods": {"bind": "(requirement, providers, explicit=None) -> AvailableProvider"},
        "contract": "Return one trusted compatible provider respecting explicit exact identity; do not rewrite trusted snapshots"},
    "Driver": {"methods": {"execute": "async (provider, request, timeout, emit) -> InvocationReport"},
        "contract": "Report correlated terminal outcome/events or separate transport error; SDK lifecycle revalidation is mandatory"},
    "Transport": {"methods": {"invoke": "async (request, emit) -> Outcome"},
        "contract": "Real Provider lifecycle, exact correlation, ordered events, valid output; failures never become verification FAIL"},
    "Store": {"methods": {"put": "(record) -> None", "get": "(run_id) -> RunRecord | None"},
        "contract": "put receives validated record; failures propagate. Relay.run does not call get; host owns retrieval contract"},
    "Observer": {"methods": {"observe": "(event) -> None"},
        "contract": "Observation does not decide verification; ordinary exceptions isolated and diagnosed"},
}


def port_cases():
    table = {
        "Catalog": {"valid": "SUCCESS", "invalid_return": "CATALOG_INVALID", "bad_manifest": "INVALID_PROVIDER_OUTPUT",
            "duplicate_identity": "PROVIDER_CONFLICT", "exception": "CATALOG_FAILURE", "iteration_failure": "CATALOG_FAILURE",
            "structured_error": "INVALID_INPUT", "generator": "CATALOG_INVALID"},
        "Binder": {"valid": "SUCCESS", "invalid_return": "PROVIDER_BINDING_MISMATCH", "bad_manifest": "INVALID_PROVIDER_OUTPUT",
            "wrong_capability": "PROVIDER_BINDING_MISMATCH", "wrong_version": "PROVIDER_BINDING_MISMATCH",
            "untrusted_transport": "PROVIDER_UNTRUSTED", "rewrite_manifest": "PROVIDER_UNTRUSTED",
            "exception": "BINDER_FAILURE", "structured_error": "INVALID_INPUT"},
        "Driver": {"valid": "SUCCESS", "invalid_return": "NODE_ERROR", "malformed_events": "NODE_ERROR",
            "wrong_correlation": "PROTOCOL_VIOLATION", "missing_terminal": "PROTOCOL_VIOLATION",
            "forged_output_error": "PROTOCOL_VIOLATION", "bad_output": "INVALID_PROVIDER_OUTPUT",
            "exception": "NODE_ERROR", "iteration_failure": "NODE_ERROR", "event_after_terminal": "PROTOCOL_VIOLATION"},
        "Transport": {"valid": "SUCCESS", "invalid_return": "NODE_ERROR", "wrong_correlation": "PROTOCOL_VIOLATION",
            "bad_output": "INVALID_PROVIDER_OUTPUT", "exception": "NODE_ERROR", "stream_failure": "NODE_ERROR",
            "duplicate_event": "PROTOCOL_VIOLATION", "wrong_sequence": "PROTOCOL_VIOLATION",
            "wrong_event_correlation": "PROTOCOL_VIOLATION"},
        "Store": {"valid": "SUCCESS", "put_exception": "PROPAGATE", "put_return": "IGNORED_RETURN",
            "get_valid": "SUCCESS", "get_absent": "SUCCESS", "get_exception": "HOST_PROPAGATE",
            "get_invalid": "HOST_CONTRACT_VIOLATION", "get_malformed": "HOST_CONTRACT_VIOLATION"},
        "Observer": {"valid": "SUCCESS", "exception": "ISOLATED", "invalid_return": "IGNORED_RETURN",
            "mutate_event": "SUCCESS"},
    }
    for port_name, variants in table.items():
        for variant, outcome in variants.items():
            yield {"id": f"port031.{port_name}.{variant}", "port": port_name, "variant": variant,
                "category": "ports031." + port_name, "expected": outcome,
                "stimulus": {"input": 11, "output": 11, "provider_id": "com.example.golden.port", "provider_version": "1"},
                "requirement": "docs/relay/architecture.md#relay-architecture-and-contracts",
                "mutation_witness": "Accept substituted identity/output, lose correlation or incurred usage, fabricate an outcome, or swallow the declared error"}
        for variant in ("cancellation", "concurrency_isolation"):
            yield {"id": f"port031.{port_name}.{variant}", "port": port_name, "variant": variant,
                "category": "ports031." + port_name, "expected": "CANCELLED_API" if variant == "cancellation" else "ISOLATED_RUNS",
                "stimulus": {"input": 11, "other_input": 22}, "requirement": "docs/relay/limitations.md",
                "mutation_witness": "Cancel the other run, store an aborted occurrence, mix inputs/run identities or reuse cancellation state"}
