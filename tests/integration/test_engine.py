from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue

from openverify import fingerprint, parse_run_record, serialize
from openverify.adapters import Registry
from openverify.adapters.demo import demo_registry, known
from openverify.engine import Engine
from openverify.errors import ProtocolError
from openverify.model import (
    Context,
    Decision,
    Edge,
    Graph,
    Guard,
    Measurement,
    Result,
    UpstreamOutput,
)
from openverify.provenance import JsonlStore, MemoryStore
from openverify.serialization import to_data
from openverify.validation import parse_object, validate_definition, validate_wire
from tests.helpers import context, definition, node


@pytest.mark.parametrize(
    "example,final", [("prose", "all"), ("generic", "envelope"), ("ai-output", "human-review")]
)
def test_examples_roundtrip_usage_lineage(example: str, final: str) -> None:
    d = definition(example)
    run = Engine(demo_registry()).run(d, context(example), opportunity_id="opportunity-1")
    assert run.final_results[final].verdict == "PASS"
    assert run.definition.id == d.id
    assert run.definition.version == d.version
    assert run.definition_fingerprint == fingerprint(d)
    assert parse_run_record(serialize(run)) == run
    validate_wire("run-record", to_data(run))
    for record in run.nodes:
        assert cast(float, record.usage["wall_time"].value) >= 0
        if record.result:
            validate_wire("result", to_data(record.result))
    if example == "prose":
        aggregate_record = next(n for n in run.nodes if n.node_id == "all")
        assert set(aggregate_record.upstream_results) == {"phrase", "length"}
        assert run.nodes[0].information != {}
    if example == "ai-output":
        routing = next(n for n in run.nodes if n.node_id == "escalate")
        assert routing.decision is not None
        assert routing.decision.destination == "human-review"


class Broken:
    version = "broken-demo"

    def execute(self, context: Context, config: Context) -> Result:
        raise RuntimeError("Sensor unavailable")


class Mutating:
    def execute(self, context: Context, config: Context) -> Result:
        context["temperature"] = -100
        config["minimum"] = -200
        return known("PASS").model_copy(
            update={"usage": {"API_calls": Measurement(unit="call", kind="EXACT", value=1)}}
        )


def test_failed_and_unregistered_adapters() -> None:
    d = definition("generic")
    registry = Registry()
    registry.register_evaluate("com.example.demo.range", Broken())
    run = Engine(registry).run(d, context("generic"), opportunity_id="o")
    result = run.final_results["envelope"]
    assert result.execution_outcome == "ERROR"
    assert cast(dict[str, JsonValue], result.output)["code"] == "EXECUTOR_ERROR"
    assert run.nodes[0].result == result
    assert run.nodes[0].executor_version == "broken-demo"
    assert parse_run_record(serialize(run)) == run
    run = Engine(Registry()).run(d, context("generic"), opportunity_id="o")
    assert (
        cast(dict[str, JsonValue], run.final_results["envelope"].output)["code"]
        == "EXECUTOR_UNSUPPORTED"
    )


def test_snapshot_isolation_and_adapter_usage() -> None:
    d = definition("generic")
    inputs = context("generic")
    registry = Registry()
    registry.register_evaluate("com.example.demo.range", Mutating())
    run = Engine(registry).run(d, inputs, opportunity_id="o")
    assert inputs["temperature"] == 21.5
    assert d.graph.nodes[0].config["minimum"] == 18
    assert run.run_inputs == inputs
    assert run.initial_context == {}
    assert run.final_results["envelope"].usage["API_calls"].value == 1
    assert "wall_time" in run.nodes[0].usage


def test_stores_snapshot_and_lineage_rejection(tmp_path: Path) -> None:
    run = Engine(demo_registry()).run(definition(), context(), opportunity_id="o")
    memory = MemoryStore()
    local = JsonlStore(tmp_path / "records.jsonl")
    memory.append(run)
    local.append(run)
    assert memory.records() == local.records() == [run]
    bad = run.model_copy(update={"final_results": {}})
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))
    bad_node = run.nodes[-1].model_copy(update={"upstream_results": {}})
    bad = run.model_copy(update={"nodes": [*run.nodes[:-1], bad_node]})
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))


class DecisionAdapter:
    def __init__(self, decision: Decision):
        self.decision = decision

    def execute(self, context: Context, config: Context) -> Decision:
        return self.decision


@pytest.mark.parametrize("kind", ["STOP_SUCCESS", "STOP_FAILURE", "RETRY", "DEFER", "CONTINUE"])
def test_control_stop_semantics(kind: str) -> None:
    decision = cast(Decision, parse_object("decision", {"protocol": "draft", "kind": kind}))
    registry = demo_registry()
    registry.register_control("com.example.test.control", DecisionAdapter(decision))
    graph = Graph(
        nodes=[
            node(id="control", kind="CONTROL", executor_ref="test.control"),
            node(
                id="later",
                kind="EVALUATE",
                executor_ref="demo.constant",
                config={"result": to_data(known("PASS"))},
            ),
        ],
        edges=[Edge(from_node="control", to_node="later")],
    )
    d = definition("generic").model_copy(update={"graph": graph})
    run = Engine(registry).run(d, context("generic"), opportunity_id="o")
    assert run.final_results["later"].disposition == (
        "EXECUTED" if kind == "CONTINUE" else "DEFERRED" if kind == "DEFER" else "SKIPPED"
    )
    assert run.nodes[0].decision == decision


def test_guard_false_and_invalid_route() -> None:
    d = definition("ai-output")
    graph = d.graph.model_copy(deep=True)
    graph.nodes[1].config["result"] = to_data(known("PASS"))
    run = Engine(demo_registry()).run(
        d.model_copy(update={"graph": graph}), context("ai-output"), opportunity_id="o"
    )
    assert run.final_results["human-review"].disposition == "SKIPPED"
    graph.nodes[2].config["destination"] = "absent"
    graph.nodes[1].config["result"] = {
        "protocol": "draft",
        "disposition": "EXECUTED",
        "execution_outcome": "SUCCESS",
        "applicability": "APPLICABLE",
        "determination": "UNKNOWN",
    }
    run = Engine(demo_registry()).run(
        d.model_copy(update={"graph": graph}), context("ai-output"), opportunity_id="o"
    )
    assert run.final_results["escalate"].execution_outcome == "ERROR"
    assert run.final_results["human-review"].disposition == "SKIPPED"


def test_judgment_schema_and_no_external_resolution() -> None:
    registry = demo_registry()
    graph = Graph(
        nodes=[
            node(
                id="judge",
                kind="EVALUATE",
                executor_ref="demo.constant",
                config={
                    "result": to_data(known("PASS").model_copy(update={"judgment": "categorical"}))
                },
            )
        ]
    )
    d = definition("generic").model_copy(
        update={"graph": graph, "run_inputs": [], "judgment_schema": {"type": "integer"}}
    )
    assert (
        Engine(registry).run(d, {}, opportunity_id="o").final_results["judge"].execution_outcome
        == "ERROR"
    )
    d = d.model_copy(update={"judgment_schema": {"$ref": "https://example.invalid/schema.json"}})
    with pytest.raises(ProtocolError, match="SCHEMA_UNSUPPORTED"):
        Engine(registry).run(d, {}, opportunity_id="o")


def test_graph_references_duplicate_cycle_and_guard() -> None:
    d = definition("generic")
    node = d.graph.nodes[0]
    for graph, code in [
        (Graph(nodes=[node, node]), "GRAPH_DUPLICATE"),
        (Graph(nodes=[node], edges=[Edge(from_node="absent", to_node=node.id)]), "GRAPH_REFERENCE"),
        (
            Graph(nodes=[node], edges=[Edge(from_node=node.id, to_node=node.id)]),
            "GRAPH_UNSUPPORTED",
        ),
        (Graph(nodes=[node], features=["DYNAMIC_EXPANSION"]), "GRAPH_UNSUPPORTED"),
        (
            Graph(
                nodes=[node, node.model_copy(update={"id": "b"})],
                edges=[
                    Edge(
                        from_node=node.id,
                        to_node="b",
                        guard=Guard(
                            source=UpstreamOutput(node_id="b", output="result"),
                            pointer="/verdict",
                            value="PASS",
                        ),
                    )
                ],
            ),
            "DATAFLOW_BINDING",
        ),
    ]:
        with pytest.raises(ProtocolError, match=code):
            validate_definition(d.model_copy(update={"graph": graph}))
