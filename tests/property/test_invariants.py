from typing import cast

from hypothesis import given
from hypothesis import strategies as st
from pydantic import JsonValue

from openverify import parse_result, serialize
from openverify.adapters.demo import known
from openverify.engine.aggregation import aggregate
from openverify.model import Graph, Result
from openverify.serialization import to_data
from openverify.validation import ordered_nodes, parse_object
from tests.helpers import handling


@given(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False))
def test_score_roundtrip(score: float) -> None:
    result = known(score=score)
    parsed = parse_result(serialize(result))
    assert parsed == result
    assert parsed.score is not None and 0 <= parsed.score <= 1


@given(
    st.lists(
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=30,
    )
)
def test_aggregate_bounds(scores: list[float]) -> None:
    inputs = [known(score=s) for s in scores]
    for reducer in ("MIN_SCORE", "MAX_SCORE", "AVERAGE"):
        result = aggregate(inputs, {"reducer": reducer, "handling": handling()})
        assert result.score is not None
        assert min(scores) <= result.score <= max(scores)


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=12),
        st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
        max_size=12,
    )
)
def test_custom_resource_maps(values: dict[str, float]) -> None:
    usage: dict[str, JsonValue] = {
        key: {"unit": "custom-unit", "kind": "EXACT", "value": value}
        for key, value in values.items()
    }
    result = parse_result({**cast(dict[str, JsonValue], to_data(known())), "usage": usage})
    assert parse_result(serialize(result)) == result


@given(
    st.integers(min_value=1, max_value=14),
    st.sets(st.tuples(st.integers(0, 13), st.integers(0, 13)), max_size=35),
)
def test_arbitrary_dag_order(size: int, pairs: set[tuple[int, int]]) -> None:
    edges: list[JsonValue] = [
        {"from_node": f"n{a}", "to_node": f"n{b}"} for a, b in sorted(pairs) if a < b < size
    ]
    nodes: list[JsonValue] = [
        {"id": f"n{i}", "kind": "EVALUATE", "executor_ref": "local"} for i in reversed(range(size))
    ]
    graph = cast(Graph, parse_object("graph", {"nodes": nodes, "edges": edges}))
    order = ordered_nodes(graph)
    assert len(order) == size
    for edge in graph.edges:
        assert order.index(edge.from_node) < order.index(edge.to_node)


json_values = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.text()
    | st.floats(allow_nan=False, allow_infinity=False),
    lambda children: (
        st.lists(children, max_size=5) | st.dictionaries(st.text(), children, max_size=5)
    ),
    max_leaves=20,
)


@given(json_values)
def test_arbitrary_output_and_optional_extension_roundtrip(value: JsonValue) -> None:
    result = cast(
        Result,
        parse_object(
            "result",
            {
                **cast(dict[str, JsonValue], to_data(known())),
                "output": value,
                "extensions": [
                    {
                        "namespace": "org.example:roundtrip",
                        "version": "1",
                        "required": False,
                        "data": value,
                    }
                ],
            },
        ),
    )
    assert parse_result(serialize(result)) == result
