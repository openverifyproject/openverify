from copy import deepcopy

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import JsonValue

from openverify import ProtocolError, parse_run_record, serialize, validate_definition
from openverify.engine import Engine
from openverify.model import Constant, UpstreamOutput
from openverify.serialization import json_equal, to_data
from tests.dataflow_helpers import Failure, derive, flow, registry
from tests.integration.test_weighted_graph_boundary import weighted_definition
from tests.property.test_invariants import json_values


@settings(max_examples=40)
@given(json_values)
def test_arbitrary_json_survives_all_bound_snapshots(value: JsonValue) -> None:
    run = Engine(registry()).run(flow(), {"x": value}, opportunity_id="property-json")
    assert json_equal(run.nodes[0].input_values["x"], value)
    assert json_equal(run.nodes[0].information["x"], value)
    assert json_equal(run.nodes[1].input_values["x"], value)
    assert json_equal(to_data(parse_run_record(serialize(run))), to_data(run))


@settings(max_examples=30)
@given(st.sampled_from(["producer", "consumer"]), st.booleans())
def test_every_required_port_has_exactly_one_declared_binding(node_id: str, remove: bool) -> None:
    d = flow()
    n = next(n for n in d.graph.nodes if n.id == node_id)
    if remove:
        n.bindings.pop("x")
    else:
        n.bindings["extra"] = Constant(value=0)
    with pytest.raises(ProtocolError, match="DATAFLOW_BINDING"):
        validate_definition(d)


@settings(max_examples=30)
@given(st.permutations(["producer", "consumer", "other"]))
def test_topological_order_is_independent_of_node_array_order(order: list[str]) -> None:
    d = flow()
    other = derive("other").model_copy(update={"bindings": {"x": Constant(value="other")}})
    nodes = {n.id: n for n in [*d.graph.nodes, other]}
    d = d.model_copy(
        update={"graph": d.graph.model_copy(update={"nodes": [nodes[n] for n in order]})}
    )
    run = Engine(registry()).run(d, {"x": "bound"}, opportunity_id="order")
    records = {r.node_id: r for r in run.nodes}
    assert records["consumer"].input_values["x"] == "bound"
    assert run.nodes.index(records["producer"]) < run.nodes.index(records["consumer"])


@settings(max_examples=30)
@given(json_values)
def test_changing_producer_output_invalidates_old_consumer_snapshot(value: JsonValue) -> None:
    run = Engine(registry()).run(flow(), {"x": value}, opportunity_id="changed")
    bad = deepcopy(run)
    new_value: JsonValue = {"replacement": [value]}
    bad.nodes[0].information["x"] = new_value
    assert bad.nodes[0].observation is not None
    bad.nodes[0].observation.outputs["x"] = new_value
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))
    changed = Engine(registry()).run(flow(), {"x": new_value}, opportunity_id="changed")
    assert json_equal(changed.nodes[1].input_values["x"], new_value)


@settings(max_examples=30)
@given(json_values)
def test_changed_initial_input_invalidates_dependent_snapshots(value: JsonValue) -> None:
    run = Engine(registry()).run(flow(), {"x": value}, opportunity_id="changed-input")
    run.run_inputs["x"] = {"replacement": [value]}
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(run))


@settings(max_examples=30)
@given(json_values)
def test_failed_producer_never_leaks_stale_value(value: JsonValue) -> None:
    r = registry()
    r.register("com.example.echo", "1", Failure())
    run = Engine(r).run(flow(), {"x": value}, context={"x": value}, opportunity_id="failed")
    assert "x" not in run.nodes[1].input_values
    resolution = run.nodes[1].input_resolutions["x"]
    assert resolution.status == "PRODUCER_ERROR"
    assert "value" not in resolution.model_fields_set
    assert run.nodes[1].state == "NONEXECUTED"


@settings(max_examples=30)
@given(st.booleans())
def test_boolean_number_substitution_on_edge_is_always_detected(flag: bool) -> None:
    run = Engine(registry()).run(flow(), {"x": flag}, opportunity_id="bool")
    run.nodes[1].input_values["x"] = int(flag)
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(run))


@settings(max_examples=30)
@given(st.booleans(), st.sampled_from(["PASS", "FAIL", "UNKNOWN", "ERROR", "SKIPPED"]))
def test_aggregate_membership_is_stable_across_result_states(mixed: bool, state: str) -> None:
    from openverify.adapters.demo import demo_registry, known
    from openverify.model import Edge, Guard, Result

    d = weighted_definition(mixed, "IGNORE", {"low": 1, "high": 3})
    if state in ("PASS", "FAIL"):
        result = known(state)
    elif state == "UNKNOWN":
        result = Result(
            disposition="EXECUTED",
            execution_outcome="SUCCESS",
            applicability="APPLICABLE",
            determination="UNKNOWN",
        )
    elif state == "ERROR":
        result = Result(disposition="EXECUTED", execution_outcome="ERROR")
    else:
        result = known(score=0)
        d.graph.edges.append(
            Edge(
                from_node="hi",
                to_node="lo",
                guard=Guard(source=Constant(value=False), pointer="", value=True),
            )
        )
    d.graph.nodes[0 if not mixed else 1].config["result"] = to_data(result)
    run = Engine(demo_registry()).run(d, {}, opportunity_id="members")
    mean = run.nodes[-1]
    assert set(mean.input_values) == {"subject", "criterion", "members", "low", "high"}
    assert d.graph.nodes[-1].aggregate_inputs == ["low", "high"]
    for name, producer in [("low", "lo"), ("high", "hi")]:
        assert mean.input_resolutions[name].source == UpstreamOutput(
            node_id=producer, output="result"
        )
