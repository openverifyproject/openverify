from typing import cast

import pytest
from pydantic import JsonValue

from openverify import ProtocolError, parse_run_record, serialize, validate_definition
from openverify.adapters.demo import demo_registry, known
from openverify.engine import Engine
from openverify.engine.aggregation import aggregate
from openverify.model import (
    Constant,
    Context,
    Edge,
    Graph,
    InputPort,
    Node,
    OutputPort,
    UpstreamOutput,
    VerificationDefinition,
)
from openverify.serialization import to_data
from tests.helpers import definition, handling, node


def weighted_definition(mixed: bool, action: str, weights: JsonValue) -> VerificationDefinition:
    members = ["low", "high"]
    lo = node(
        id="lo",
        kind="EVALUATE",
        executor_ref="demo.constant",
        config={"result": to_data(known(score=0))},
    )
    hi = node(
        id="hi",
        kind="EVALUATE",
        executor_ref="demo.constant",
        config={"result": to_data(known(score=1))},
    )
    mean = node(
        id="mean",
        kind="AGGREGATE",
        executor_ref="standard.aggregate",
        config={"reducer": "WEIGHTED_AVERAGE", "handling": handling(action), "weights": weights},
    )
    mean.inputs.extend(
        InputPort(name=n, schema={"type": "object"}, required=True, on_unavailable="BLOCK")
        for n in members
    )
    mean.bindings.update(
        low=UpstreamOutput(node_id="lo", output="result"),
        high=UpstreamOutput(node_id="hi", output="result"),
    )
    mean.bindings["members"] = Constant(value=cast(JsonValue, members))
    mean = mean.model_copy(update={"aggregate_inputs": members})
    nodes: list[Node] = [lo, hi, mean]
    edges = [Edge(from_node="lo", to_node="mean"), Edge(from_node="hi", to_node="mean")]
    if mixed:
        nodes.insert(
            0,
            node(
                id="derive",
                kind="DERIVE",
                executor_ref="demo.length",
                config={"key": "text", "output_key": "length"},
            ).model_copy(
                update={
                    "inputs": [
                        InputPort(
                            name="text",
                            schema={"type": "string"},
                            required=True,
                            on_unavailable="BLOCK",
                        )
                    ],
                    "bindings": {"text": Constant(value="some text")},
                    "outputs": [
                        OutputPort(name="length", schema={"type": "integer"}, role="INFORMATION")
                    ],
                }
            ),
        )
        edges.insert(0, Edge(from_node="derive", to_node="mean"))
    return definition("generic").model_copy(
        update={"run_inputs": [], "graph": Graph(nodes=nodes, edges=edges)}
    )


@pytest.mark.parametrize("mixed", [False, True])
@pytest.mark.parametrize("action", ["IGNORE", "REJECT"])
@pytest.mark.parametrize("broken", [False, True])
def test_weighted_membership_and_weights_ignore_edge_order_and_derive_state(
    mixed: bool, action: str, broken: bool
) -> None:
    d = weighted_definition(mixed, action, {"low": 1, "high": 3})
    from tests.dataflow_helpers import Failure

    registry = demo_registry()
    if broken:
        registry.register("com.example.demo.length", "1", Failure())
    for edges in [d.graph.edges, list(reversed(d.graph.edges))]:
        run = Engine(registry).run(
            d.model_copy(update={"graph": d.graph.model_copy(update={"edges": edges})}),
            {},
            opportunity_id="weights",
        )
        assert run.final_results["mean"].score == 0.75
        mean = run.nodes[-1]
        assert set(mean.input_values) == {"subject", "criterion", "members", "low", "high"}
        assert parse_run_record(serialize(run)) == run


@pytest.mark.parametrize(
    "weights",
    [
        None,
        {},
        [],
        [1, 3],
        {"low": 1},
        {"low": True, "high": 1},
        {"low": -1, "high": 2},
        {"low": 0, "high": 0},
        {"other": 1, "high": 3},
    ],
)
def test_weight_identity_and_values_validated_before_execution(weights: JsonValue) -> None:
    with pytest.raises(ProtocolError, match="AGGREGATE_CONFIG"):
        validate_definition(weighted_definition(False, "IGNORE", weights))


def test_membership_mismatch_rejected() -> None:
    d = weighted_definition(False, "REJECT", {"low": 1, "high": 3})
    d.graph.nodes[-1].aggregate_inputs.append("absent")
    with pytest.raises(ProtocolError, match="AGGREGATE_CONFIG"):
        validate_definition(d)


@pytest.mark.parametrize("action", ["IGNORE", "REJECT"])
def test_direct_weighted_error_policy_uses_explicit_inputs(action: str) -> None:
    from openverify.model import Result

    inputs = [Result(disposition="EXECUTED", execution_outcome="ERROR"), known(score=0.5)]
    config: Context = {
        "reducer": "WEIGHTED_AVERAGE",
        "handling": handling(action),
        "weights": [7, 1],
    }
    if action == "IGNORE":
        assert aggregate(inputs, config).score == 0.5
    else:
        with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
            aggregate(inputs, config)


def test_direct_weight_association_survives_aligned_permutation() -> None:
    config: Context = {"reducer": "WEIGHTED_AVERAGE", "handling": handling(), "weights": [1, 3]}
    assert aggregate([known(score=0), known(score=1)], config).score == 0.75
    assert aggregate([known(score=1), known(score=0)], {**config, "weights": [3, 1]}).score == 0.75


def test_weights_follow_member_identity_while_evidence_follows_authored_order() -> None:
    from openverify.model import Evidence

    d = weighted_definition(False, "REJECT", {"low": 1, "high": 3})
    for n, score, message in [(d.graph.nodes[0], 0.0, "low"), (d.graph.nodes[1], 1.0, "high")]:
        n.config["result"] = to_data(
            known(score=score).model_copy(update={"evidence": [Evidence(message=message)]})
        )
    aggregate_node = d.graph.nodes[-1]
    aggregate_node.bindings["members"] = Constant(value=["high", "low"])
    d.graph.nodes[-1] = aggregate_node.model_copy(update={"aggregate_inputs": ["high", "low"]})
    run = Engine(demo_registry()).run(d, {}, opportunity_id="weight-order")
    result = run.final_results["mean"]
    assert result.score == 0.75
    assert [e.message for e in result.evidence] == ["high", "low"]
