"""Remaining VCP/provider error axes and custom computation boundaries."""

from typing import Literal, cast

import pytest

from openverify import Graph, ProtocolError, Relay
from openverify.authoring import constant
from openverify.model import (
    Activation,
    Capability,
    Context,
    ExecutionObservation,
    Measurement,
    OperationRequirement,
    Result,
    Selection,
)
from openverify.relay import passing_gate, provider
from openverify.relay.templates import text_graph
from openverify.standard import standard_catalog
from openverify.standard.common import OBJECT, STRING, object_schema
from tests.relay.helpers import evaluator_graph, judge_provider, known, local_catalog


@pytest.mark.parametrize(
    "result",
    [
        Result(disposition="EXECUTED", execution_outcome="ERROR"),
        Result(
            disposition="EXECUTED",
            execution_outcome="SUCCESS",
            applicability="APPLICABLE",
            determination="UNKNOWN",
        ),
        Result(disposition="EXECUTED", execution_outcome="SUCCESS", applicability="NOT_APPLICABLE"),
        Result(disposition="SKIPPED"),
        Result(disposition="DEFERRED"),
        Result(disposition="CANCELLED"),
    ],
)
def test_guardrail_never_allows_exceptional_results(result: Result) -> None:
    run = Relay(catalog=local_catalog(judge_provider(result))).run_sync(
        evaluator_graph(), inputs={}
    )
    assert not passing_gate(run)


def test_fail_does_not_stop_independent_work() -> None:
    catalog = local_catalog(judge_provider(known("FAIL")))
    graph = evaluator_graph()
    graph.evaluate("other", "com.example.judge", inputs={"x": constant("hello", STRING)})
    run = Relay(catalog=catalog).run_sync(graph, inputs={})
    assert len(run.record.provider_bindings) == 2
    assert all(n.state == "SUCCESS" for n in run.record.nodes)


def test_invalid_semantic_output_retains_measured_usage() -> None:
    @provider(
        provider_id="com.example.invalid",
        capability_id="com.example.judge",
        kind="EVALUATE",
        input_schema=OBJECT,
        output_schema=OBJECT,
        config_schema=OBJECT,
    )
    async def invalid(inputs: Context, config: Context) -> ExecutionObservation:
        return ExecutionObservation(
            outputs={
                "result": {
                    "protocol": "draft",
                    "disposition": "EXECUTED",
                    "execution_outcome": "SUCCESS",
                    "applicability": "APPLICABLE",
                    "determination": "UNKNOWN",
                    "verdict": "PASS",
                }
            },
            usage={
                "tokens": Measurement(unit="token", kind="EXACT", value=8),
                "wall_time": Measurement(unit="ms", kind="EXACT", value=2),
            },
        )

    run = Relay(catalog=local_catalog(invalid)).run_sync(evaluator_graph(), inputs={})
    assert run.results["check"].execution_outcome == "ERROR"
    assert run.usage["check"]["tokens"].value == 8
    assert run.usage["check"]["wall_time"].unit == "ms"
    assert run.usage["check"]["relay_wall_time"].unit == "s"


@pytest.mark.parametrize("role", ["ACTIVATION", "SELECTION"])
def test_no_occurrence_policies(role: Literal["ACTIVATION", "SELECTION"]) -> None:
    @provider(
        provider_id="com.example.policy",
        capability_id="com.example.policy",
        kind=role,
        input_schema=OBJECT,
        output_schema=OBJECT,
        config_schema=OBJECT,
    )
    async def policy(inputs: Context, config: Context) -> Activation | Selection:
        return (
            Activation(outcome="DO_NOT_ACTIVATE", reason="Not eligible")
            if role == "ACTIVATION"
            else Selection(subjects=[], reason="Not selected")
        )

    graph = text_graph()
    requirement = OperationRequirement(capability_id="com.example.policy", capability_version="1")
    graph.execution_policy = graph.execution_policy.model_copy(
        update={role.lower(): Capability(operation=requirement)}
    )
    catalog = standard_catalog()
    catalog.register(policy)
    relay = Relay(catalog=catalog)
    with pytest.raises(ProtocolError, match="NO_OCCURRENCE"):
        relay.run_sync(graph, inputs={"text": "Migration Rollback"})


def test_custom_aggregate_receives_exact_ordered_members() -> None:
    seen: list[Context] = []

    @provider(
        provider_id="com.example.aggregate",
        capability_id="com.example.aggregate",
        kind="AGGREGATE",
        input_schema=OBJECT,
        output_schema=object_schema({"result": OBJECT}),
        config_schema=OBJECT,
    )
    async def aggregate(inputs: Context, config: Context) -> Result:
        seen.append(inputs)
        return known("FAIL" if cast(Context, inputs["second"])["verdict"] == "FAIL" else "PASS")

    graph = Graph("custom-aggregate")
    text = graph.input("text", STRING)
    a = graph.evaluate(
        "a", "openverify.text", inputs={"text": text}, config={"required": ["Migration"]}
    )
    b = graph.evaluate(
        "b", "openverify.text", inputs={"text": text}, config={"prohibited": ["TODO"]}
    )
    graph.aggregate(
        "custom", {"second": b.result, "first": a.result}, capability="com.example.aggregate"
    )
    catalog = standard_catalog()
    catalog.register(aggregate)
    result = Relay(catalog=catalog).run_sync(graph, inputs={"text": "Migration TODO"})
    assert result.results["custom"].verdict == "FAIL"
    assert seen[0]["members"] == ["second", "first"]
    assert set(seen[0]) == {"second", "first", "members", "subject", "criterion"}
