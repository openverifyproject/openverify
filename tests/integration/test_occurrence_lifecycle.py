"""Policy/occurrence regressions derived from the written VCP lifecycle contract."""

from copy import deepcopy
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from openverify import ProtocolError, parse_result, parse_run_record, serialize, validate_definition
from openverify.adapters.demo import known
from openverify.engine import Cancellation, Engine
from openverify.model import (
    AdmissionPolicy,
    Capability,
    Constant,
    Context,
    Decision,
    Edge,
    Evidence,
    ExecutionObservation,
    ExternalReference,
    Graph,
    Guard,
    OperationRequirement,
    Result,
    RunInput,
    UpstreamOutput,
    VerificationDefinition,
)
from openverify.serialization import json_equal, to_data
from tests.dataflow_helpers import Failure, flow, input_port, registry
from tests.helpers import node


class Policy:
    version = "policy-1"

    def __init__(self, outcome: Context):
        self.outcome = outcome
        self.calls: list[Context] = []

    def execute(self, inputs: Context, config: Context) -> Context:
        self.calls.append(deepcopy(inputs))
        return deepcopy(self.outcome)


def custom(role: str, definition: VerificationDefinition) -> VerificationDefinition:
    operation = OperationRequirement(capability_id=f"com.example.{role}", capability_version="1")
    policy = (
        AdmissionPolicy(operation=operation)
        if role == "admission"
        else Capability(operation=operation)
    )
    return definition.model_copy(
        update={"execution_policy": definition.execution_policy.model_copy(update={role: policy})}
    )


@pytest.mark.parametrize("stage", ["activation", "selection"])
def test_no_occurrence_stops_before_next_policy(stage: str) -> None:
    d = custom(stage, flow())
    r = registry()
    p = Policy(
        {"outcome": "DO_NOT_ACTIVATE", "reason": "event absent"}
        if stage == "activation"
        else {"subjects": [], "reason": "not selected"}
    )
    r.register(f"com.example.{stage}", "1", p)
    # An unregistered later policy demonstrates it is never invoked.
    d = custom("selection" if stage == "activation" else "admission", d)
    assert Engine(r).attempt(d, {"x": 0}, opportunity_id="o") is None
    assert p.calls == [{}]
    with pytest.raises(ProtocolError, match="NO_OCCURRENCE"):
        Engine(r).run(d, {"x": 0}, opportunity_id="o")


@pytest.mark.parametrize("outcome", ["RUN", "SKIP", "DEFER"])
def test_all_policy_stages_and_exact_admission_boundary(outcome: str) -> None:
    d = flow()
    r = registry()
    adapters: list[Policy] = []
    for stage, value in (
        ("activation", {"outcome": "ACTIVATE", "reason": "event"}),
        ("selection", {"subjects": [to_data(d.subject)], "reason": "subject"}),
        ("admission", {"outcome": outcome, "reason": "resource policy"}),
    ):
        d = custom(stage, d)
        adapter = Policy(cast(Context, value))
        adapters.append(adapter)
        r.register(f"com.example.{stage}", "1", adapter)
    if outcome != "RUN":
        r.operations.pop(("com.example.echo", "1"))
        r.operations.pop(("com.example.echo.judge", "1"))
    run = Engine(r).run(d, {"x": 0}, opportunity_id="o")
    assert all(p.calls == [{}] for p in adapters)
    assert run.admission.outcome == outcome
    assert [p.role for p in run.policy_evaluations] == ["ACTIVATION", "SELECTION", "ADMISSION"]
    assert all(p.executor_version == "policy-1" for p in run.policy_evaluations)
    assert parse_run_record(serialize(run)) == run
    if outcome == "RUN":
        assert run.final_results["consumer"].verdict == "PASS"
    else:
        for record in run.nodes:
            assert record.result is not None
            assert record.result.disposition == ("SKIPPED" if outcome == "SKIP" else "DEFERRED")
            assert record.reason == f"ADMISSION_{outcome}"
            assert record.observation is None and record.executor_ref is None


@pytest.mark.parametrize("role", ["activation", "selection", "admission"])
def test_policy_inputs_have_exact_typed_sources_and_no_ambient_context(role: str) -> None:
    d = custom(role, flow({"type": "integer"}))
    policy = getattr(d.execution_policy, role)
    policy.inputs.extend(
        [input_port("value", {"type": "integer"}), input_port("constant"), input_port("ref")]
    )
    policy.bindings.update(
        value=RunInput(name="x"),
        constant=Constant(value=False),
        ref=ExternalReference(reference=d.subject),
    )
    outcomes: dict[str, Context] = {
        "activation": {"outcome": "ACTIVATE", "reason": "event"},
        "selection": {"subjects": [to_data(d.subject)], "reason": "scope"},
        "admission": {"outcome": "RUN", "reason": "admit"},
    }
    p = Policy(outcomes[role])
    r = registry()
    r.register(f"com.example.{role}", "1", p)
    run = Engine(r).run(d, {"x": 8}, context={"budget": 999, "value": "stale"}, opportunity_id="o")
    assert json_equal(p.calls[0], {"value": 8, "constant": False, "ref": to_data(d.subject)})
    record = next(e for e in run.policy_evaluations if e.role == role.upper())
    assert record.input_values == p.calls[0]
    assert all(v.status == "AVAILABLE" for v in record.input_resolutions.values())
    bad = deepcopy(run)
    next(e for e in bad.policy_evaluations if e.role == role.upper()).input_values["budget"] = 999
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))


@pytest.mark.parametrize(
    "mode",
    ["unbound", "unknown-run", "upstream", "operation", "config", "schema", "duplicate", "mixed"],
)
def test_invalid_policy_structure_prevents_every_invocation(mode: str) -> None:
    d = custom("admission", flow())
    p = d.execution_policy.admission
    p.inputs.append(input_port("required"))
    p.bindings["required"] = Constant(value=0)
    if mode == "unbound":
        p.bindings.clear()
    elif mode == "unknown-run":
        p.bindings["required"] = RunInput(name="absent")
    elif mode == "upstream":
        p.bindings["required"] = UpstreamOutput(node_id="producer", output="x")
    elif mode == "operation":
        p = p.model_copy(
            update={"operation": OperationRequirement(capability_id="bad", capability_version="")}
        )
    elif mode in ("config", "schema"):
        p = p.model_copy(
            update={"config_schema": {"type": "integer" if mode == "config" else "invented"}}
        )
    elif mode == "duplicate":
        p.inputs.append(input_port("required"))
    else:
        p = p.model_copy(update={"strategy": "ALWAYS"})
    d = d.model_copy(
        update={"execution_policy": d.execution_policy.model_copy(update={"admission": p})}
    )
    activation = Policy({"outcome": "ACTIVATE", "reason": "event"})
    d = custom("activation", d)
    r = registry()
    r.register("com.example.activation", "1", activation)
    with pytest.raises(ProtocolError):
        Engine(r).attempt(d, {"x": 0}, opportunity_id="o")
    assert activation.calls == []


@pytest.mark.parametrize("mode", ["missing", "invalid"])
def test_unavailable_required_policy_input_has_no_fallback(mode: str) -> None:
    d = custom("admission", flow())
    d = d.model_copy(update={"run_inputs": [input_port("x", required=False)]})
    p = d.execution_policy.admission
    p.inputs.append(input_port("value", {"type": "integer"}))
    p.bindings["value"] = RunInput(name="x")
    adapter = Policy({"outcome": "RUN", "reason": "admit"})
    r = registry()
    r.register("com.example.admission", "1", adapter)
    with pytest.raises(ProtocolError, match="POLICY_INPUT"):
        Engine(r).attempt(
            d, {} if mode == "missing" else {"x": "bad"}, context={"value": 8}, opportunity_id="o"
        )
    assert adapter.calls == []


@pytest.mark.parametrize("disposition", ["SKIPPED", "DEFERRED", "CANCELLED"])
def test_invoked_evaluator_cannot_claim_nonexecution(disposition: str) -> None:
    class Pretend:
        def execute(self, inputs: Context, config: Context) -> Result:
            return Result.model_validate({"disposition": disposition})

    r = registry()
    r.register("com.example.echo.judge", "1", Pretend())
    run = Engine(r).run(flow(), {"x": 0}, opportunity_id="o")
    result = run.final_results["consumer"]
    assert result.disposition == "EXECUTED" and result.execution_outcome == "ERROR"
    assert result.verdict is None
    assert run.nodes[1].reason == "OUTPUT_INVALID"


@pytest.mark.parametrize(
    "kind,disposition,reason",
    [
        ("CONTINUE", "EXECUTED", None),
        ("STOP_SUCCESS", "SKIPPED", "CONTROL_STOP"),
        ("STOP_FAILURE", "SKIPPED", "CONTROL_STOP"),
        ("DEFER", "DEFERRED", "CONTROL_DEFER"),
        ("RETRY", "SKIPPED", "RETRY_REQUESTED"),
    ],
)
def test_control_effects_preserve_stronger_state(
    kind: str, disposition: str, reason: str | None
) -> None:
    class Control:
        def execute(self, inputs: Context, config: Context) -> Decision:
            return Decision.model_validate({"kind": kind})

    d = flow()
    control = node(id="control", kind="CONTROL", executor_ref="control")
    d.graph.nodes.insert(0, control)
    d.graph.edges.insert(0, Edge(from_node="control", to_node="producer"))
    r = registry()
    r.register("com.example.control", "1", Control())
    run = Engine(r).run(d, {"x": 0}, opportunity_id="o")
    assert run.nodes[0].decision is not None and run.nodes[0].decision.kind == kind
    assert run.final_results["consumer"].disposition == disposition
    assert run.nodes[-1].reason == reason
    assert parse_run_record(serialize(run)) == run


def test_route_excludes_exclusive_branch_and_preserves_join_and_independent_work() -> None:
    class Route:
        def execute(self, inputs: Context, config: Context) -> Decision:
            return Decision(kind="ROUTE", destination="selected")

    d = flow()
    nodes = [node(id="route", kind="CONTROL", executor_ref="route")]
    for name in ("selected", "excluded", "child", "join", "independent"):
        nodes.append(d.graph.nodes[0].model_copy(update={"id": name}))
    d = d.model_copy(
        update={
            "graph": Graph(
                nodes=nodes,
                edges=[
                    Edge(from_node=a, to_node=b)
                    for a, b in [
                        ("route", "selected"),
                        ("route", "excluded"),
                        ("excluded", "child"),
                        ("selected", "join"),
                        ("child", "join"),
                    ]
                ],
            )
        }
    )
    r = registry()
    r.register("com.example.route", "1", Route())
    run = Engine(r).run(d, {"x": 0}, opportunity_id="o")
    for record in run.nodes:
        if record.node_id in ("excluded", "child"):
            assert record.reason == "ROUTE_EXCLUDED"
            assert record.result is not None and record.result.disposition == "SKIPPED"
        else:
            assert record.state == "SUCCESS"


def test_false_guard_and_producer_error_have_different_nonexecution_causes() -> None:
    d = flow()
    d.graph.edges[0] = Edge(
        from_node="producer",
        to_node="consumer",
        guard=Guard(source=Constant(value=False), pointer="", value=True),
    )
    run = Engine(registry()).run(d, {"x": 0}, opportunity_id="o")
    assert run.nodes[-1].reason == "GUARD_FALSE"
    assert run.final_results["consumer"].verdict is None
    r = registry()
    r.register("com.example.echo", "1", Failure())
    run = Engine(r).run(flow(), {"x": "old"}, context={"x": "older"}, opportunity_id="o")
    assert run.nodes[-1].reason == "INPUT_UNAVAILABLE"
    assert "x" not in run.nodes[-1].input_values


@pytest.mark.parametrize("phase", ["BEFORE_START", "RUNNING", "EXCEPTION"])
def test_explicit_cancellation_prevents_or_interrupts_execution(phase: str) -> None:
    token = Cancellation()

    class Cancelling:
        def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
            token.cancel("host request")
            if phase == "EXCEPTION":
                raise RuntimeError("interrupted")
            return ExecutionObservation(outputs={"x": inputs["x"]})

    r = registry()
    r.register("com.example.echo", "1", Cancelling())
    if phase == "BEFORE_START":
        token.cancel("host request")
    run = Engine(r).run(flow(), {"x": 0}, opportunity_id="o", cancellation=token)
    assert run.cancellation is not None
    assert run.cancellation.phase == ("BEFORE_START" if phase == "BEFORE_START" else "RUNNING")
    assert run.nodes[0].state == ("NONEXECUTED" if phase == "BEFORE_START" else "CANCELLED")
    assert run.nodes[1].state == "NONEXECUTED"
    assert all(n.reason == "CANCELLATION" and not n.information for n in run.nodes)
    assert all(r.disposition == "CANCELLED" for r in run.final_results.values())
    assert parse_run_record(serialize(run)) == run
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(run.model_copy(update={"cancellation": None})))


@given(
    st.sampled_from(["SKIP", "DEFER"]),
    st.sampled_from(["EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED"]),
)
def test_admission_lifecycle_disposition_cannot_be_rewritten(
    admission: str, disposition: str
) -> None:
    d = custom("admission", flow())
    r = registry()
    r.register("com.example.admission", "1", Policy({"outcome": admission, "reason": "policy"}))
    run = Engine(r).run(d, {"x": 0}, opportunity_id="o")
    expected = "SKIPPED" if admission == "SKIP" else "DEFERRED"
    if disposition == expected:
        return
    bad = deepcopy(run)
    result = (
        Result.model_validate({"disposition": disposition})
        if disposition != "EXECUTED"
        else known("FAIL")
    )
    bad.nodes[0] = bad.nodes[0].model_copy(update={"result": result})
    bad.final_results[bad.nodes[0].node_id] = result
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))


@pytest.mark.parametrize("mode", ["inactive", "unselected", "admission", "reason"])
def test_contradictory_occurrence_policy_provenance_is_rejected(mode: str) -> None:
    run = Engine(registry()).run(flow(), {"x": 0}, opportunity_id="o")
    raw = cast(Context, to_data(run))
    evaluations = cast(list[Context], raw["policy_evaluations"])
    if mode == "inactive":
        evaluations[0]["outcome"] = {"outcome": "DO_NOT_ACTIVATE", "reason": "absent"}
    elif mode == "unselected":
        evaluations[1]["outcome"] = {"subjects": [], "reason": "absent"}
    elif mode == "admission":
        raw["admission"] = {"outcome": "DEFER", "reason": "policy"}
    else:
        nodes = cast(list[Context], raw["nodes"])
        nodes[0]["state"] = "NONEXECUTED"
        nodes[0]["reason"] = "ADMISSION_SKIP"
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(raw)


def test_policy_definition_is_inspectable() -> None:
    validate_definition(custom("admission", flow()))


@pytest.mark.parametrize("role", ["activation", "selection", "admission"])
@pytest.mark.parametrize("mode", ["wrong-role", "exception", "not-json"])
def test_policy_errors_do_not_become_occurrences(role: str, mode: str) -> None:
    class InvalidPolicy:
        def execute(self, inputs: Context, config: Context) -> Context | Decision:
            if mode == "exception":
                raise RuntimeError("policy unavailable")
            if mode == "not-json":
                return Decision(kind="DEFER")
            return {"outcome": "FAIL", "reason": "invalid for policy role"}

    r = registry()
    r.register(f"com.example.{role}", "1", InvalidPolicy())
    with pytest.raises(
        ProtocolError, match="POLICY_ERROR" if mode == "exception" else "POLICY_OUTPUT"
    ):
        Engine(r).attempt(custom(role, flow()), {"x": 0}, opportunity_id="o")


def test_selection_cannot_substitute_another_subject_or_duplicate_identity() -> None:
    d = custom("selection", flow())
    r = registry()
    for subjects in (
        [to_data(d.subject), to_data(d.subject)],
        [to_data(d.subject.model_copy(update={"id": "another"}))],
    ):
        r.register("com.example.selection", "1", Policy({"subjects": subjects, "reason": "scope"}))
        with pytest.raises(ProtocolError, match="POLICY_OUTPUT"):
            Engine(r).attempt(d, {"x": 0}, opportunity_id="o")


@pytest.mark.parametrize("mode", ["not-applicable", "unknown", "fail", "exception"])
def test_executed_semantic_states_never_become_nonexecution(mode: str) -> None:
    class Evaluator:
        def execute(self, inputs: Context, config: Context) -> Result:
            if mode == "exception":
                raise RuntimeError("provider failure")
            if mode == "not-applicable":
                return Result(
                    disposition="EXECUTED",
                    execution_outcome="SUCCESS",
                    applicability="NOT_APPLICABLE",
                )
            if mode == "unknown":
                return Result(
                    disposition="EXECUTED",
                    execution_outcome="SUCCESS",
                    applicability="APPLICABLE",
                    determination="UNKNOWN",
                )
            return known("FAIL")

    r = registry()
    r.register("com.example.echo.judge", "1", Evaluator())
    run = Engine(r).run(flow(), {"x": 0}, opportunity_id="o")
    result = run.final_results["consumer"]
    assert result.disposition == "EXECUTED"
    assert result.execution_outcome == ("ERROR" if mode == "exception" else "SUCCESS")
    assert result.applicability == (
        None
        if mode == "exception"
        else "NOT_APPLICABLE"
        if mode == "not-applicable"
        else "APPLICABLE"
    )
    assert result.verdict == ("FAIL" if mode == "fail" else None)


@pytest.mark.parametrize("disposition", ["SKIPPED", "DEFERRED", "CANCELLED"])
def test_standalone_nonexecution_still_accepts_diagnostic_evidence(disposition: str) -> None:
    result = Result.model_validate(
        {
            "disposition": disposition,
            "evidence": [to_data(Evidence(message="Host recorded nonexecution"))],
        }
    )
    assert parse_result(serialize(result)) == result


def test_portable_sampling_record_does_not_require_reference_bucket_identity() -> None:
    d = flow().model_copy(update={"graph": Graph(nodes=[])})
    d = d.model_copy(
        update={
            "execution_policy": d.execution_policy.model_copy(
                update={"admission": AdmissionPolicy(strategy="PROBABILITY", probability=0.5)}
            )
        }
    )
    run = Engine(registry()).run(d, {"x": 0}, opportunity_id="o")
    other = run.admission.model_copy(
        update={"outcome": "SKIP" if run.admission.outcome == "RUN" else "RUN"}
    )
    evaluations = list(run.policy_evaluations)
    evaluations[-1] = evaluations[-1].model_copy(update={"outcome": other})
    parse_run_record(
        serialize(run.model_copy(update={"admission": other, "policy_evaluations": evaluations}))
    )


def test_cancellation_after_a_completed_node_does_not_rewrite_it() -> None:
    token = Cancellation()

    class CancellingJudge:
        def execute(self, inputs: Context, config: Context) -> Result:
            token.cancel()
            return known("PASS")

    r = registry()
    r.register("com.example.echo.judge", "1", CancellingJudge())
    run = Engine(r).run(flow(), {"x": 0}, opportunity_id="o", cancellation=token)
    assert run.nodes[0].state == "SUCCESS"
    assert run.nodes[0].information == {"x": 0}
    assert run.nodes[1].state == "CANCELLED"
    assert run.nodes[1].result is not None and run.nodes[1].result.disposition == "CANCELLED"
    assert run.nodes[1].observation is not None
    assert run.nodes[1].result.verdict is None
    bad = deepcopy(run)
    bad.nodes[1] = bad.nodes[1].model_copy(update={"result": known("PASS")})
    bad.final_results["consumer"] = known("PASS")
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))
