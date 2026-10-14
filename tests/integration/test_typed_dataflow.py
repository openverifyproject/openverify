from copy import deepcopy
from typing import cast

import pytest
from pydantic import JsonValue

from openverify import (
    ProtocolError,
    inspect_definition,
    parse_definition,
    parse_run_record,
    serialize,
    validate_definition,
    validate_executable_definition,
)
from openverify.adapters import Registry
from openverify.adapters.demo import known
from openverify.engine import Engine
from openverify.model import (
    Constant,
    Context,
    Edge,
    ExecutionError,
    ExecutionObservation,
    Graph,
    Guard,
    InputPort,
    Measurement,
    OperationRequirement,
    OutputPort,
    RunInput,
    UpstreamOutput,
)
from openverify.serialization import json_equal, to_data
from tests.dataflow_helpers import Failure, derive, flow, input_port, registry
from tests.helpers import definition, node


@pytest.mark.parametrize("value", [None, False, 0, 0.0, "", [], {}])
def test_explicit_values_survive_bound_execution_and_provenance(value: JsonValue) -> None:
    run = Engine(registry()).run(flow(), {"x": value}, opportunity_id="values")
    assert json_equal(run.nodes[1].input_values["x"], value)
    assert json_equal(to_data(parse_run_record(serialize(run))), to_data(run))
    assert json_equal(run.run_inputs, {"x": value})


def test_unrelated_producers_with_same_name_cannot_change_binding() -> None:
    d = flow()
    other = derive("unrelated").model_copy(update={"bindings": {"x": Constant(value="other")}})
    for nodes in [[other, *d.graph.nodes], [*d.graph.nodes, other]]:
        run = Engine(registry()).run(
            d.model_copy(update={"graph": d.graph.model_copy(update={"nodes": nodes})}),
            {"x": "chosen"},
            opportunity_id="order",
        )
        consumer = next(r for r in run.nodes if r.node_id == "consumer")
        assert consumer.input_values["x"] == "chosen"


@pytest.mark.parametrize("mutation", ["producer", "run", "snapshot", "binding", "bool-number"])
def test_provenance_detects_changes_along_dataflow(mutation: str) -> None:
    run = Engine(registry()).run(flow(), {"x": 0}, opportunity_id="tamper")
    bad = deepcopy(run)
    if mutation == "producer":
        bad.nodes[0].information["x"] = 1
        assert bad.nodes[0].observation is not None
        bad.nodes[0].observation.outputs["x"] = 1
    elif mutation == "run":
        bad.run_inputs["x"] = 1
    elif mutation == "snapshot":
        bad.nodes[1].input_values["unbound"] = 42
    elif mutation == "binding":
        bad.nodes[1].input_resolutions["x"] = (
            bad.nodes[1].input_resolutions["x"].model_copy(update={"source": RunInput(name="x")})
        )
    else:
        bad.nodes[1].input_values["x"] = False
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))


def test_failed_producer_cannot_read_stale_run_or_ambient_value() -> None:
    r = registry()
    r.register("com.example.echo", "1", Failure())
    run = Engine(r).run(
        flow(), {"x": "stale run input"}, context={"x": "ambient stale"}, opportunity_id="failed"
    )
    assert run.nodes[1].state == "NONEXECUTED"
    assert run.nodes[1].reason == "INPUT_UNAVAILABLE"
    assert run.nodes[1].input_resolutions["x"].status == "PRODUCER_ERROR"
    assert "x" not in run.nodes[1].input_values
    assert run.final_results["consumer"].disposition == "SKIPPED"
    assert run.initial_context == {"x": "ambient stale"}


class ObservationAdapter:
    def __init__(self, observation: ExecutionObservation):
        self.observation = observation

    def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
        return self.observation


@pytest.mark.parametrize("mode", ["invalid", "missing", "error", "nonexecuted"])
def test_required_information_availability_reasons(mode: str) -> None:
    d = flow({"type": "integer"})
    observed = ExecutionObservation(outputs={"x": False} if mode == "invalid" else {})
    if mode == "error":
        observed = observed.model_copy(
            update={"error": ExecutionError(code="com.example.failure", message="Unavailable")}
        )
    if mode == "nonexecuted":
        guard = Guard(source=Constant(value=False), pointer="", value=True)
        before = derive("before").model_copy(update={"bindings": {"x": Constant(value=0)}})
        d = d.model_copy(
            update={
                "graph": Graph(
                    nodes=[before, *d.graph.nodes],
                    edges=[
                        Edge(from_node="before", to_node="producer", guard=guard),
                        *d.graph.edges,
                    ],
                )
            }
        )
    r = registry()
    r.register("com.example.echo", "1", ObservationAdapter(observed))
    run = Engine(r).run(d, {"x": 0}, opportunity_id="availability")
    consumer = next(n for n in run.nodes if n.node_id == "consumer")
    expected = {
        "invalid": "INVALID",
        "missing": "OUTPUT_MISSING",
        "error": "PRODUCER_ERROR",
        "nonexecuted": "PRODUCER_NOT_EXECUTED",
    }[mode]
    assert consumer.input_resolutions["x"].status == expected
    assert consumer.state == "NONEXECUTED"


def test_optional_explicit_omit_and_default() -> None:
    d = flow()
    producer = d.graph.nodes[0]
    producer = producer.model_copy(
        update={
            "inputs": [
                input_port("omitted", required=False),
                InputPort(
                    name="x",
                    schema=True,
                    required=False,
                    on_unavailable="DEFAULT",
                    default=Constant(value=None),
                ),
            ],
            "bindings": {},
        }
    )
    d = d.model_copy(
        update={
            "run_inputs": [],
            "graph": d.graph.model_copy(update={"nodes": [producer, d.graph.nodes[1]]}),
        }
    )
    run = Engine(registry()).run(d, {}, opportunity_id="optional")
    assert run.nodes[0].input_values == {"x": None}
    assert run.nodes[0].input_resolutions["omitted"].status == "ABSENT"
    assert run.nodes[0].input_resolutions["x"].used_default
    assert json_equal(to_data(run), to_data(parse_run_record(serialize(run))))


@pytest.mark.parametrize("supplied", [{}, {"x": 0, "extra": 1}, {"x": False}])
def test_run_input_validation_precedes_invocation(supplied: Context) -> None:
    with pytest.raises(ProtocolError, match="RUN_INPUT"):
        Engine(Registry()).run(flow({"type": "number"}), supplied, opportunity_id="run-input")


@pytest.mark.parametrize(
    "defect",
    [
        "unbound",
        "run",
        "producer",
        "output",
        "target",
        "forward",
        "type",
        "port",
        "operation",
        "config",
    ],
)
def test_graph_validation_precedes_invocation(defect: str) -> None:
    d = flow({"type": "integer"})
    p, c = d.graph.nodes
    if defect == "unbound":
        c.bindings.pop("x")
    elif defect == "run":
        p.bindings["x"] = RunInput(name="absent")
    elif defect == "producer":
        c.bindings["x"] = UpstreamOutput(node_id="absent", output="x")
    elif defect == "output":
        c.bindings["x"] = UpstreamOutput(node_id="producer", output="absent")
    elif defect == "target":
        c.bindings["absent"] = Constant(value=0)
    elif defect == "forward":
        d.graph.edges.clear()
    elif defect == "type":
        c.inputs[-1] = input_port("x", {"type": "boolean"})
    elif defect == "port":
        p.outputs.append(p.outputs[0])
    elif defect == "config":
        d.graph.nodes[0] = p.model_copy(update={"config_schema": {"type": "null"}})
    if defect == "operation":
        d.graph.nodes[0] = p.model_copy(
            update={
                "operation": OperationRequirement(
                    capability_id="ConcreteProvider", capability_version="1"
                )
            }
        )
    with pytest.raises(ProtocolError):
        Engine(Registry()).run(d, {"x": 0}, opportunity_id="invalid")


def test_schema_overlap_is_checked_at_runtime_without_false_subsumption_claim() -> None:
    d = flow({"type": "integer"})
    producer = d.graph.nodes[0]
    producer.outputs[0] = OutputPort(name="x", schema={"type": "integer"}, role="INFORMATION")
    consumer = d.graph.nodes[1]
    consumer.inputs[-1] = input_port("x", {"type": "integer", "minimum": 10})
    validate_executable_definition(d)
    run = Engine(registry()).run(d, {"x": 1}, opportunity_id="runtime-types")
    assert run.nodes[1].input_resolutions["x"].status == "INVALID"
    assert run.nodes[1].state == "NONEXECUTED"


@pytest.mark.parametrize("kind", ["DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"])
def test_usage_survives_invalid_semantic_output_for_every_kind(kind: str) -> None:
    n = node(id="attempt", kind=kind, executor_ref="bad.output")
    if kind == "DERIVE":
        n = n.model_copy(
            update={
                "outputs": [OutputPort(name="x", schema={"type": "integer"}, role="INFORMATION")]
            }
        )
    if kind == "AGGREGATE":
        source = node(
            id="source",
            kind="EVALUATE",
            executor_ref="demo.constant",
            config={"result": to_data(known("PASS"))},
        )
        n.inputs.append(input_port("check", {"type": "object"}))
        n.bindings["check"] = UpstreamOutput(node_id="source", output="result")
        n.bindings["members"] = Constant(value=["check"])
        n = n.model_copy(update={"aggregate_inputs": ["check"]})
        nodes = [source, n]
        edges = [Edge(from_node="source", to_node="attempt")]
    else:
        nodes = [n]
        edges = []
    d = definition("generic").model_copy(
        update={"run_inputs": [], "graph": Graph(nodes=nodes, edges=edges)}
    )
    usage = {"API_calls": Measurement(unit="call", kind="EXACT", value=2)}
    obs = ExecutionObservation(outputs={p.name: False for p in n.outputs}, usage=usage)
    r = Registry()
    r.register("com.example.bad.output", "1", ObservationAdapter(obs))
    r.register(
        "com.example.demo.constant",
        "1",
        ObservationAdapter(ExecutionObservation(outputs={"result": to_data(known("PASS"))})),
    )
    run = Engine(r).run(d, {}, opportunity_id="usage")
    last = run.nodes[-1]
    assert last.state == "ERROR" and last.observation is not None
    assert last.observation.usage["API_calls"].value == 2
    assert last.usage["wall_time"].value is not None
    assert last.information == {}
    assert parse_run_record(serialize(run)) == run


def test_invalid_judgment_retains_result_reported_usage() -> None:
    d = flow().model_copy(update={"judgment_schema": {"type": "integer"}})
    r = registry()
    candidate = known("PASS").model_copy(
        update={
            "judgment": "wrong",
            "usage": {"tokens": Measurement(unit="token", kind="EXACT", value=7)},
        }
    )
    r.register(
        "com.example.echo.judge",
        "1",
        ObservationAdapter(
            ExecutionObservation(outputs={"result": to_data(candidate)}, usage=candidate.usage)
        ),
    )
    run = Engine(r).run(d, {"x": None}, opportunity_id="judgment")
    assert run.nodes[-1].reason == "JUDGMENT_INVALID"
    observed = run.nodes[-1].observation
    assert observed is not None and observed.usage["tokens"].value == 7


def test_explicit_null_judgment_is_validated() -> None:
    d = flow().model_copy(update={"judgment_schema": {"type": "integer"}})
    r = registry()
    candidate = known("PASS").model_copy(update={"judgment": None})
    r.register(
        "com.example.echo.judge",
        "1",
        ObservationAdapter(ExecutionObservation(outputs={"result": to_data(candidate)})),
    )
    run = Engine(r).run(d, {"x": None}, opportunity_id="null-judgment")
    assert run.nodes[-1].reason == "JUDGMENT_INVALID"


def test_subject_and_criterion_are_authoritative_explicit_inputs() -> None:
    d = flow()
    d.graph.nodes[1].config["criterion"] = {"id": "hidden-drift"}
    run = Engine(registry()).run(d, {"x": None}, opportunity_id="meaning")
    assert run.nodes[1].input_values["criterion"] == to_data(d.criterion)
    d.graph.nodes[1].bindings["criterion"] = Constant(value={"id": "other", "description": "Other"})
    with pytest.raises(ProtocolError, match="SEMANTIC_BINDING"):
        validate_definition(d)


def test_typed_run_input_guard_and_output_guard() -> None:
    d = flow()
    d.graph.edges[0] = Edge(
        from_node="producer",
        to_node="consumer",
        guard=Guard(source=RunInput(name="x"), pointer="", value=False),
    )
    assert (
        Engine(registry()).run(d, {"x": False}, opportunity_id="guard").nodes[-1].state == "SUCCESS"
    )
    assert (
        Engine(registry()).run(d, {"x": 0}, opportunity_id="guard").nodes[-1].state == "NONEXECUTED"
    )
    d.graph.edges[0] = Edge(
        from_node="producer",
        to_node="consumer",
        guard=Guard(source=UpstreamOutput(node_id="producer", output="x"), pointer="", value=0),
    )
    assert Engine(registry()).run(d, {"x": 0}, opportunity_id="guard").nodes[-1].state == "SUCCESS"


def test_inspection_exposes_sources_outputs_capability_and_consumers() -> None:
    d = flow()
    inspect_definition(d)
    info = inspect_definition(d)
    nodes = cast(dict[str, JsonValue], info["nodes"])
    producer = cast(dict[str, JsonValue], nodes["producer"])
    assert producer["consumers"] == {"x": ["consumer"]}
    assert parse_definition(serialize(d)) == d


def test_exact_capability_version_does_not_fall_back() -> None:
    d = flow()
    d.graph.nodes[0] = d.graph.nodes[0].model_copy(
        update={
            "operation": OperationRequirement(
                capability_id="com.example.echo", capability_version="2"
            )
        }
    )
    run = Engine(registry()).run(d, {"x": 0}, opportunity_id="version")
    assert run.nodes[0].reason == "EXECUTOR_UNSUPPORTED"
    assert run.nodes[1].state == "NONEXECUTED"


class OrderedAggregate:
    def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
        members = cast(list[str], inputs["members"])
        return ExecutionObservation(
            outputs={
                "result": to_data(
                    known("PASS").model_copy(
                        update={
                            "output": [
                                cast(dict[str, JsonValue], inputs[name])["score"]
                                for name in members
                            ]
                        }
                    )
                )
            }
        )


def test_custom_aggregate_receives_explicit_order_without_object_order_assumptions() -> None:
    from openverify.adapters.demo import demo_registry
    from tests.integration.test_weighted_graph_boundary import weighted_definition

    d = weighted_definition(False, "REJECT", {"low": 1, "high": 3})
    agg = d.graph.nodes[-1]
    agg.bindings["members"] = Constant(value=["high", "low"])
    d.graph.nodes[-1] = agg.model_copy(
        update={
            "aggregate_inputs": ["high", "low"],
            "operation": OperationRequirement(
                capability_id="com.example.custom.aggregate", capability_version="1"
            ),
            "config": {},
        }
    )
    r = demo_registry()
    r.register("com.example.custom.aggregate", "1", OrderedAggregate())
    run = Engine(r).run(d, {}, opportunity_id="custom-order")
    assert json_equal(run.final_results["mean"].output, [1, 0])


def test_usage_disagreement_invalidates_output_without_erasing_observed_usage() -> None:
    d = flow()
    r = registry()
    candidate = known("PASS").model_copy(
        update={"usage": {"calls": Measurement(unit="call", kind="EXACT", value=10)}}
    )
    r.register(
        "com.example.echo.judge",
        "1",
        ObservationAdapter(
            ExecutionObservation(
                outputs={"result": to_data(candidate)},
                usage={"calls": Measurement(unit="call", kind="EXACT", value=2)},
            )
        ),
    )
    run = Engine(r).run(d, {"x": None}, opportunity_id="usage-conflict")
    assert run.nodes[-1].reason == "OUTPUT_INVALID"
    assert run.nodes[-1].observation is not None
    assert run.nodes[-1].observation.usage["calls"].value == 2


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "not-a-type"},
        {"$ref": "#/$defs/missing"},
        {"$defs": {"x": {"$id": "nested", "type": "string"}}},
        {"$dynamicRef": "#x"},
        {"$ref": "#/default", "default": {}},
    ],
)
def test_unsupported_or_invalid_schemas_are_rejected_upfront(schema: dict[str, JsonValue]) -> None:
    d = flow().model_copy(update={"judgment_schema": schema})
    with pytest.raises(ProtocolError, match="SCHEMA_UNSUPPORTED"):
        validate_definition(d)


def test_self_contained_schema_reference_validates_runtime_output() -> None:
    schema: dict[str, JsonValue] = {
        "$defs": {"value": {"type": "integer"}},
        "$ref": "#/$defs/value",
    }
    run = Engine(registry()).run(flow(schema), {"x": 2}, opportunity_id="schema-local")
    assert run.nodes[1].state == "SUCCESS"


@pytest.mark.parametrize("value", [{}, [], False, None, 0])
def test_invalid_semantic_guard_operand_is_a_protocol_error(value: JsonValue) -> None:
    d = definition("generic")
    source = d.graph.nodes[0]
    downstream = derive("other").model_copy(update={"bindings": {"x": Constant(value=0)}})
    d = d.model_copy(
        update={
            "graph": Graph(
                nodes=[source, downstream],
                edges=[
                    Edge(
                        from_node=source.id,
                        to_node="other",
                        guard=Guard(
                            source=UpstreamOutput(node_id=source.id, output="result"),
                            pointer="/verdict",
                            value=value,
                        ),
                    )
                ],
            )
        }
    )
    with pytest.raises(ProtocolError, match="GRAPH_REFERENCE"):
        validate_definition(d)


def test_run_input_default_and_optional_absence_are_explicit() -> None:
    d = flow()
    d = d.model_copy(
        update={
            "run_inputs": [
                InputPort(
                    name="x",
                    schema=True,
                    required=False,
                    on_unavailable="DEFAULT",
                    default=Constant(value=False),
                )
            ]
        }
    )
    run = Engine(registry()).run(d, {}, opportunity_id="run-default")
    assert run.run_inputs == {}
    assert run.nodes[0].input_values["x"] is False
    assert parse_run_record(serialize(run)) == run


def test_external_reference_remains_exact_and_unfetched() -> None:
    from openverify.model import ArtifactRef, ExternalReference

    d = flow()
    ref = ArtifactRef(
        id="measurement",
        type="application/json",
        locator={"opaque": "https://not-fetched.invalid/data"},
    )
    d.graph.nodes[0].bindings["x"] = ExternalReference(reference=ref)
    d = d.model_copy(update={"run_inputs": []})
    run = Engine(registry()).run(d, {}, opportunity_id="ref")
    assert run.nodes[0].input_values["x"] == to_data(ref)
    assert run.nodes[1].input_values["x"] == to_data(ref)


def test_invalid_policy_information_is_rejected_before_node_invocation() -> None:
    d = flow()
    policy = d.execution_policy.activation
    policy.inputs.append(input_port("risk"))
    policy.bindings["risk"] = RunInput(name="missing")
    with pytest.raises(ProtocolError, match="DATAFLOW_BINDING"):
        Engine(Registry()).run(d, {"x": 0}, opportunity_id="policy")
    policy.bindings["risk"] = Constant(value=0)
    with pytest.raises(ProtocolError, match="POLICY_UNSUPPORTED"):
        Engine(Registry()).run(d, {"x": 0}, opportunity_id="policy")


def test_error_bookkeeping_does_not_bypass_refined_result_output_schema() -> None:
    d = flow()
    first = d.graph.nodes[1]
    first.outputs[0] = OutputPort(
        name="result",
        schema={
            "type": "object",
            "properties": {"execution_outcome": {"const": "SUCCESS"}},
            "required": ["execution_outcome"],
        },
        role="RESULT",
    )
    next_node = node(id="control", kind="CONTROL", executor_ref="unused.control")
    next_node.inputs.append(input_port("result"))
    next_node.bindings["result"] = UpstreamOutput(node_id="consumer", output="result")
    d.graph.nodes.append(next_node)
    d.graph.edges.append(Edge(from_node="consumer", to_node="control"))
    r = registry()
    r.register("com.example.echo.judge", "1", Failure())
    run = Engine(r).run(d, {"x": 0}, opportunity_id="error-port")
    assert run.nodes[-1].input_resolutions["result"].status == "INVALID"
    assert run.nodes[-1].state == "NONEXECUTED"


def test_optional_failure_fallback_requires_explicit_default_binding_policy() -> None:
    d = flow()
    consumer = d.graph.nodes[1]
    consumer.inputs[-1] = InputPort(
        name="x",
        schema=True,
        required=False,
        on_unavailable="DEFAULT",
        default=Constant(value=False),
    )
    r = registry()
    r.register("com.example.echo", "1", Failure())
    run = Engine(r).run(d, {"x": "stale"}, opportunity_id="explicit-fallback")
    resolution = run.nodes[1].input_resolutions["x"]
    assert resolution.status == "PRODUCER_ERROR" and resolution.used_default
    assert run.nodes[1].input_values["x"] is False
    assert run.nodes[1].state == "SUCCESS"
    assert parse_run_record(serialize(run)) == run


def test_guard_over_open_schema_fields_and_local_schema_references() -> None:
    schema: dict[str, JsonValue] = {
        "type": "object",
        "properties": {"a": {"$ref": "#/$defs/int"}},
        "$defs": {"int": {"type": "integer"}},
    }
    d = flow(schema)
    for path, value in [("/a", 1), ("/other", 2)]:
        d.graph.edges[0] = Edge(
            from_node="producer",
            to_node="consumer",
            guard=Guard(
                source=UpstreamOutput(node_id="producer", output="x"), pointer=path, value=value
            ),
        )
        run = Engine(registry()).run(d, {"x": {"a": 1, "other": 2}}, opportunity_id="guard-local")
        assert run.nodes[-1].state == "SUCCESS"


def test_invalid_observed_evidence_does_not_erase_valid_incurred_usage() -> None:
    from openverify.model import Evidence

    d = flow()
    r = registry()
    observed = ExecutionObservation(
        outputs={"x": 0},
        evidence=[Evidence()],
        usage={"calls": Measurement(unit="call", kind="EXACT", value=1)},
    )
    r.register("com.example.echo", "1", ObservationAdapter(observed))
    run = Engine(r).run(d, {"x": 0}, opportunity_id="invalid-evidence")
    assert run.nodes[0].reason == "EVIDENCE_EMPTY"
    assert run.nodes[0].observation is not None
    assert run.nodes[0].observation.usage["calls"].value == 1
    assert run.nodes[1].state == "NONEXECUTED"
    assert parse_run_record(serialize(run)) == run
