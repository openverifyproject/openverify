import json
from typing import cast

import pytest
from pydantic import JsonValue

from openverify import ProtocolError, serialize
from openverify.adapters import Registry
from openverify.adapters.demo import known
from openverify.engine import Engine
from openverify.engine.aggregation import aggregate
from openverify.model import Context, Edge, Graph, Node, Result, VerificationDefinition
from openverify.validation import parse_definition, validate_definition, validate_wire
from tests.helpers import definition, handling


class Deriver:
    def __init__(self, broken: bool):
        self.broken = broken
        self.calls = 0

    def execute(self, context: Context, config: Context) -> Context:
        self.calls += 1
        if self.broken:
            raise RuntimeError("Sensor unavailable")
        return {}


def weighted_definition(mixed: bool, action: str, weights: JsonValue) -> VerificationDefinition:
    return definition("generic").model_copy(
        update={
            "graph": Graph(
                nodes=[
                    Node(id="lo", kind="DERIVE" if mixed else "EVALUATE", executor_ref="local"),
                    Node(id="hi", kind="EVALUATE", executor_ref="local"),
                    Node(
                        id="mean",
                        kind="AGGREGATE",
                        executor_ref="standard.aggregate",
                        config={
                            "reducer": "WEIGHTED_AVERAGE",
                            "handling": handling(action),
                            "weights": weights,
                        },
                    ),
                ],
                edges=[Edge(from_node="lo", to_node="mean"), Edge(from_node="hi", to_node="mean")],
            )
        }
    )


@pytest.mark.parametrize("mixed", [False, True])
@pytest.mark.parametrize("action", ["IGNORE", "REJECT"])
@pytest.mark.parametrize("broken", [False, True])
def test_weighted_graph_rejection_is_independent_of_order_and_executor_state(
    mixed: bool, action: str, broken: bool
) -> None:
    d = weighted_definition(mixed, action, [1] if mixed else [1, 3])
    adapter = Deriver(broken)
    registry = Registry()
    registry.register_derive("local", adapter)
    for reversed_edges in [False, True]:
        edges = list(reversed(d.graph.edges)) if reversed_edges else d.graph.edges
        changed = d.model_copy(update={"graph": d.graph.model_copy(update={"edges": edges})})
        # Structural recognition is distinct from unsupported portable execution.
        raw = cast(dict[str, JsonValue], json.loads(serialize(changed)))
        validate_wire("verification-definition", raw)
        raw = dict(reversed(list(raw.items())))
        with pytest.raises(ProtocolError) as error:
            validate_definition(changed)
        assert error.value.code == "GRAPH_UNSUPPORTED"
        with pytest.raises(ProtocolError) as error:
            parse_definition(raw)
        assert error.value.code == "GRAPH_UNSUPPORTED"
        with pytest.raises(ProtocolError) as error:
            Engine(registry).run(changed, {}, opportunity_id="weighted")
        assert error.value.code == "GRAPH_UNSUPPORTED"
    assert adapter.calls == 0


@pytest.mark.parametrize("weights", [None, {}, {"lo": 1}, [], [True], ["1"], [-1], [0]])
def test_malformed_weight_config_precedes_unsupported_capability(weights: JsonValue) -> None:
    d = weighted_definition(True, "IGNORE", weights)
    with pytest.raises(ProtocolError, match="AGGREGATE_CONFIG"):
        validate_definition(d)


def test_missing_weight_config_is_deterministic() -> None:
    d = weighted_definition(True, "IGNORE", [1])
    nodes = list(d.graph.nodes)
    config = dict(nodes[-1].config)
    del config["weights"]
    nodes[-1] = nodes[-1].model_copy(update={"config": config})
    with pytest.raises(ProtocolError, match="AGGREGATE_CONFIG"):
        validate_definition(
            d.model_copy(update={"graph": d.graph.model_copy(update={"nodes": nodes})})
        )


@pytest.mark.parametrize("action", ["IGNORE", "REJECT"])
def test_direct_weighted_error_policy_uses_explicit_inputs(action: str) -> None:
    inputs = [Result(disposition="EXECUTED", execution_outcome="ERROR"), known(score=0.5)]
    config: Context = {
        "reducer": "WEIGHTED_AVERAGE",
        "handling": handling(action),
        "weights": [7, 1],
    }
    if action == "IGNORE":
        assert aggregate(inputs, config).score == 0.5
    else:
        with pytest.raises(ProtocolError) as error:
            aggregate(inputs, config)
        assert error.value.code == "AGGREGATE_INPUT"
        assert error.value.message == "Rejected ERROR input"


def test_direct_weight_association_survives_aligned_permutation() -> None:
    config: Context = {"reducer": "WEIGHTED_AVERAGE", "handling": handling(), "weights": [1, 3]}
    assert aggregate([known(score=0), known(score=1)], config).score == 0.75
    assert aggregate([known(score=1), known(score=0)], {**config, "weights": [3, 1]}).score == 0.75
