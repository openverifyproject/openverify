"""Pure transitions, readiness, reducers, and portable authoring."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from openverify import Graph, ProtocolError, parse_definition
from openverify.model import Context, Severity
from openverify.relay.core.aggregation import reduce_results
from openverify.relay.core.readiness import ready_wave
from openverify.relay.core.state import RunState
from openverify.serialization import to_data
from openverify.validation import HANDLING
from tests.relay.helpers import known


def config(reducer: str, handling: str = "REJECT") -> Context:
    return {"reducer": reducer, "handling": {k: handling for k in HANDLING}}


def test_transitions_and_barriers() -> None:
    state = RunState({"n": "PENDING"})
    for phase in ("READY", "RUNNING", "TERMINAL"):
        state.transition("n", phase)
    with pytest.raises(ValueError):
        state.transition("n", "READY")
    graph = Graph("barrier")
    a = graph.derive("a", "com.example.echo", outputs={"x": True})
    graph.control("control", "com.example.control")
    graph.derive("b", "com.example.echo", outputs={"x": True})
    assert [n.id for n in ready_wave(graph.build().graph, set(), 8)] == [a.id]
    assert [n.id for n in ready_wave(graph.build().graph, {a.id}, 8)] == ["control"]


@pytest.mark.parametrize(
    ("reducer", "verdict"), [("ALL", "FAIL"), ("ANY", "PASS"), ("MAJORITY", "PASS")]
)
def test_logical_reducers(reducer: str, verdict: str) -> None:
    value = reduce_results(
        {
            "members": ["x", "y", "z"],
            "x": to_data(known()),
            "y": to_data(known("FAIL")),
            "z": to_data(known()),
        },
        config(reducer),
    )
    assert value.verdict == verdict


@pytest.mark.parametrize(
    ("reducer", "expected"),
    [("MIN_SCORE", 0.2), ("MAX_SCORE", 0.8), ("AVERAGE", 0.5), ("WEIGHTED_AVERAGE", 0.65)],
)
def test_numeric_reducers(reducer: str, expected: float) -> None:
    settings = config(reducer)
    if reducer == "WEIGHTED_AVERAGE":
        settings["weights"] = {"x": 1, "y": 3}
    inputs: Context = {
        "members": ["x", "y"],
        "x": to_data(known(score=0.2)),
        "y": to_data(known(score=0.8)),
    }
    result = reduce_results(inputs, settings)
    assert result.score == pytest.approx(expected)
    assert result.verdict is None


def test_severity_and_exceptional_membership() -> None:
    settings = config("WORST_SEVERITY")
    settings["severity_domain"] = {
        "id": "risk",
        "levels": [{"label": "low", "rank": 1}, {"label": "high", "rank": 2}],
    }
    inputs: Context = {
        "members": ["a", "b"],
        "a": to_data(known(severity={"domain": "risk", "label": "low"})),
        "b": to_data(known(severity={"domain": "risk", "label": "high"})),
    }
    assert reduce_results(inputs, settings).severity == Severity(domain="risk", label="high")
    inputs["b"] = {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": "ERROR"}
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        reduce_results(inputs, settings)
    settings["handling"] = {k: "IGNORE" for k in HANDLING}
    assert reduce_results(inputs, settings).severity == Severity(domain="risk", label="low")


@given(st.floats(min_value=0, max_value=1, allow_nan=False))
def test_identical_means_and_weight_identity(score: float) -> None:
    inputs: Context = {
        "members": ["second", "first"],
        "second": to_data(known(score=score)),
        "first": to_data(known(score=score)),
    }
    settings = config("WEIGHTED_AVERAGE")
    settings["weights"] = {"first": 3, "second": 7}
    assert reduce_results(inputs, settings).score == score


@pytest.mark.parametrize("reducer", ["ALL", "ANY", "MAJORITY", "AVERAGE"])
def test_empty_rejected(reducer: str) -> None:
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        reduce_results({"members": []}, config(reducer))


def test_tie_and_missing_verdict_rejected() -> None:
    inputs: Context = {"members": ["a", "b"], "a": to_data(known()), "b": to_data(known("FAIL"))}
    with pytest.raises(ProtocolError, match="Majority tie"):
        reduce_results(inputs, config("MAJORITY"))
    inputs["b"] = {
        "protocol": "draft",
        "disposition": "EXECUTED",
        "execution_outcome": "SUCCESS",
        "applicability": "APPLICABLE",
        "determination": "KNOWN",
        "score": 0.8,
    }
    with pytest.raises(ProtocolError, match="MISSING"):
        reduce_results(inputs, config("ALL"))


def test_builder_portable_deterministic_and_invalid_graphs() -> None:
    graph = Graph("portable")
    x = graph.input("x", {"type": "string"})
    source = graph.derive(
        "source", "com.example.echo", inputs={"x": x}, outputs={"x": {"type": "string"}}
    )
    graph.evaluate("check", "com.example.judge", inputs={"x": source["x"]})
    assert graph.build() == parse_definition(graph.to_json())
    assert graph.to_json() == graph.to_json()
    graph.validate()
    assert graph.inspect()["id"] == "portable"
    graph.edge(source, source)
    with pytest.raises(ProtocolError, match="GRAPH_UNSUPPORTED"):
        graph.build()


def test_duplicate_and_expansion_reject() -> None:
    graph = Graph("duplicate")
    graph.input("x", True)
    graph.input("x", True)
    with pytest.raises(ProtocolError):
        graph.build()
    graph = Graph("feature").build()
    raw = to_data(graph)
    assert isinstance(raw, dict) and isinstance(raw["graph"], dict)
    raw["graph"]["features"] = ["DYNAMIC_EXPANSION"]
    with pytest.raises(ProtocolError, match="GRAPH_UNSUPPORTED"):
        parse_definition(raw)
