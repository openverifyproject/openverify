"""End-to-end state/dataflow/policy/provider semantics through public Relay."""

import asyncio
from pathlib import Path

import pytest

from openverify import Graph, ProtocolError, Relay, parse_run_record
from openverify.authoring import constant
from openverify.model import (
    AdmissionPolicy,
    Capability,
    Constant,
    Context,
    ExecutionPolicy,
    Guard,
    InputPort,
    OperationRequirement,
    Result,
)
from openverify.provider import Outcome, ProviderEvent
from openverify.relay import RuntimeConfig, passing_gate, provider
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.adapters.jsonl import JsonlStore
from openverify.relay.adapters.logging import CallbackObserver
from openverify.relay.ports.binding import identity
from openverify.relay.templates import guardrail_graph, text_graph
from openverify.standard.common import OBJECT, STRING, object_schema
from tests.relay.helpers import (
    Scripted,
    echo_graph,
    echo_provider,
    evaluator_graph,
    judge_provider,
    local_catalog,
)


def test_raw_json_equivalence_and_input_snapshot() -> None:
    relay = Relay()
    graph = text_graph()
    inputs: Context = {"text": "Migration Rollback TODO"}
    first = relay.run_sync(graph, inputs=inputs)
    second = relay.run_sync(graph.to_json(), inputs=inputs)
    assert first.results == second.results
    assert first.results["all"].verdict == "FAIL"
    assert first.results["prohibited"].evidence[0].structured_data == {
        "code": "prohibited_text",
        "term": "TODO",
        "start": 19,
        "end": 23,
        "line": 1,
        "column": 20,
    }
    inputs["text"] = "mutated"
    assert first.record.run_inputs["text"] == "Migration Rollback TODO"
    assert parse_run_record(first.to_json()) == first.record
    assert not passing_gate(first)
    assert passing_gate(relay.run_sync(graph, inputs={"text": "Migration Rollback"}))


@pytest.mark.parametrize("inputs", [{}, {"text": 2}, {"text": "ok", "undeclared": True}])
def test_inputs_rejected_before_invocation(inputs: Context) -> None:
    with pytest.raises(ProtocolError, match="RUN_INPUT"):
        Relay().run_sync(text_graph(), inputs=inputs)


def test_catalog_binding_and_explicit_precedence() -> None:
    catalog = local_catalog()
    with pytest.raises(ProtocolError, match="PROVIDER_CONFLICT"):
        catalog.register(echo_provider())
    catalog.register(echo_provider(provider_id="org.example.echo"))
    with pytest.raises(ProtocolError, match="PROVIDER_AMBIGUOUS"):
        Relay(catalog=catalog).run_sync(echo_graph(), inputs={"x": 1})
    chosen = catalog.providers()[0]
    requirement = OperationRequirement(capability_id="com.example.echo", capability_version="1")
    binding = identity(chosen, requirement)
    relay = Relay(catalog=catalog, config=RuntimeConfig(bindings={"echo": binding}))
    record = relay.run_sync(echo_graph(), inputs={"x": 1}).record
    assert record.provider_bindings == {"echo": binding}
    assert record.nodes[0].executor_ref == binding.provider_id
    with pytest.raises(ProtocolError, match="CAPABILITY_UNAVAILABLE"):
        Relay(catalog=Catalog()).run_sync(echo_graph(), inputs={"x": 1})
    wrong = binding.model_copy(update={"capability_version": "2"})
    with pytest.raises(ProtocolError, match="PROVIDER_BINDING_MISMATCH"):
        Relay(catalog=catalog, config=RuntimeConfig(bindings={"echo": wrong})).run_sync(
            echo_graph(), inputs={"x": 1}
        )


@pytest.mark.parametrize(
    "items",
    [
        [],
        [
            Outcome(invocation_id="x", state="COMPLETED", output={"x": 1}),
            Outcome(invocation_id="x", state="COMPLETED", output={"x": 1}),
        ],
        [ProviderEvent(invocation_id="x", sequence=2, kind="progress", payload={})],
        [Outcome(invocation_id="x", state="CANCELLED")],
    ],
)
def test_invalid_provider_stream_is_error_not_fail(items: list[ProviderEvent | Outcome]) -> None:
    catalog = Catalog()
    catalog.register(Scripted(items))
    run = Relay(catalog=catalog).run_sync(echo_graph(), inputs={"x": 1})
    assert run.results["echo"].execution_outcome == "ERROR"
    assert run.results["echo"].verdict is None


def test_schema_invalid_output_preserves_usage_and_blocks_data() -> None:
    catalog = Catalog()
    manifest = echo_provider().manifest()
    capability = manifest.capabilities[0].model_copy(
        update={"output_schema": object_schema({"x": STRING})}
    )
    manifest = manifest.model_copy(update={"capabilities": [capability]})
    usage: Context = {"tokens": {"kind": "EXACT", "unit": "token", "value": 3}}
    catalog.register(
        Scripted(
            [
                Outcome(
                    invocation_id="x", state="COMPLETED", output={"x": False}, resource_usage=usage
                )
            ],
            manifest,
        )
    )
    graph = echo_graph()
    # A required upstream INFORMATION input is unavailable after provider rejection.
    from openverify.authoring import Ref
    from openverify.model import UpstreamOutput

    graph.derive(
        "consumer",
        "com.example.echo",
        inputs={"x": Ref(UpstreamOutput(node_id="echo", output="x"), True)},
        outputs={"x": True},
    )
    run = Relay(catalog=catalog).run_sync(graph, inputs={"x": False})
    node = run.record.nodes[0]
    assert node.provider_output_error is not None
    assert node.observation is not None and node.observation.outputs == {"x": False}
    assert node.usage["tokens"].value == 3
    assert run.record.nodes[1].reason == "INPUT_UNAVAILABLE"
    assert run.record.nodes[1].input_resolutions["x"].status == "INVALID"


@pytest.mark.parametrize("field", ["input_schema", "config_schema"])
def test_provider_schema_rejection_precedes_actual_invocation(field: str) -> None:
    base = echo_provider()
    cap = base.manifest().capabilities[0].model_copy(update={field: False})
    catalog = Catalog()
    catalog.register(Scripted([], base.manifest().model_copy(update={"capabilities": [cap]})))
    run = Relay(catalog=catalog).run_sync(echo_graph(), inputs={"x": 1})
    assert run.record.nodes[0].state == "ERROR"
    assert not run.record.provider_bindings
    assert run.record.nodes[0].reason == (
        "INVALID_INPUT" if field == "input_schema" else "INVALID_CONFIG"
    )


def test_invalid_vcp_result_and_decision() -> None:
    invalid = Result(disposition="SKIPPED")
    run = Relay(catalog=local_catalog(judge_provider(invalid))).run_sync(
        evaluator_graph(), inputs={}
    )
    assert run.results["check"].execution_outcome == "ERROR"
    catalog = Catalog()
    manifest = echo_provider().manifest()
    cap = manifest.capabilities[0].model_copy(
        update={"input_schema": OBJECT, "output_schema": OBJECT}
    )
    catalog.register(
        Scripted(
            [
                Outcome(
                    invocation_id="x",
                    state="COMPLETED",
                    output={
                        "decision": {"protocol": "draft", "kind": "ROUTE", "destination": "absent"}
                    },
                )
            ],
            manifest.model_copy(update={"capabilities": [cap]}),
        )
    )
    graph = Graph("control")
    graph.control("c", "com.example.echo")
    record = Relay(catalog=catalog).run_sync(graph, inputs={}).record
    assert record.nodes[0].reason == "GRAPH_REFERENCE"


def test_usage_survives_duplicate_terminal_after_actual_completed_outcome() -> None:
    catalog = Catalog()
    completed = Outcome(
        invocation_id="x",
        state="COMPLETED",
        output={"x": 1},
        resource_usage={"tokens": {"unit": "token", "kind": "EXACT", "value": 9}},
    )
    catalog.register(Scripted([completed, completed]))
    run = Relay(catalog=catalog).run_sync(echo_graph(), inputs={"x": 1})
    assert run.results["echo"].execution_outcome == "ERROR"
    assert run.usage["echo"]["tokens"].value == 9


@pytest.mark.parametrize(
    ("decision", "disposition", "reason"),
    [
        ("STOP_SUCCESS", "SKIPPED", "CONTROL_STOP"),
        ("STOP_FAILURE", "SKIPPED", "CONTROL_STOP"),
        ("RETRY", "SKIPPED", "RETRY_REQUESTED"),
        ("DEFER", "DEFERRED", "CONTROL_DEFER"),
    ],
)
def test_control_termination(decision: str, disposition: str, reason: str) -> None:
    @provider(
        provider_id="com.example.control",
        capability_id="com.example.control",
        kind="CONTROL",
        input_schema=OBJECT,
        output_schema=OBJECT,
        config_schema=OBJECT,
    )
    async def control(inputs: Context, config: Context) -> Context:
        return {"decision": {"protocol": "draft", "kind": decision}}

    catalog = local_catalog()
    catalog.register(control)
    graph = Graph("stop")
    graph.control("c", "com.example.control")
    graph.derive("later", "com.example.echo", inputs={"x": constant(1)}, outputs={"x": True})
    run = Relay(catalog=catalog).run_sync(graph, inputs={})
    assert run.results["later"].disposition == disposition
    assert run.record.nodes[1].reason == reason
    assert run.record.nodes[0].result is None


def test_routes_shared_joins_and_guard_false_without_implicit_propagation() -> None:
    @provider(
        provider_id="com.example.route",
        capability_id="com.example.route",
        kind="CONTROL",
        input_schema=OBJECT,
        output_schema=OBJECT,
        config_schema=OBJECT,
    )
    async def route(inputs: Context, config: Context) -> Context:
        return {"decision": {"protocol": "draft", "kind": "ROUTE", "destination": "a"}}

    catalog = local_catalog()
    catalog.register(route)
    graph = Graph("routing")
    c = graph.control("c", "com.example.route")
    a = graph.derive(
        "a", "com.example.echo", inputs={"x": constant(1)}, outputs={"x": True}, dependencies=[c]
    )
    b = graph.derive(
        "b", "com.example.echo", inputs={"x": constant(2)}, outputs={"x": True}, dependencies=[c]
    )
    graph.derive(
        "join",
        "com.example.echo",
        inputs={"x": constant(3)},
        outputs={"x": True},
        dependencies=[a, b],
    )
    run = Relay(catalog=catalog).run_sync(graph, inputs={})
    assert run.record.nodes[2].reason == "ROUTE_EXCLUDED"
    assert run.record.nodes[3].information == {"x": 3}
    enabled = graph.input("enabled", {"type": "boolean"})
    graph.edge(c, a, guard=Guard(source=enabled.source, pointer="", value=True))
    run = Relay(catalog=catalog).run_sync(graph, inputs={"enabled": False})
    assert next(n for n in run.record.nodes if n.node_id == "a").reason == "GUARD_FALSE"
    assert next(n for n in run.record.nodes if n.node_id == "join").state == "SUCCESS"


def test_custom_policies_nonoccurrence_admission_and_defaults() -> None:
    @provider(
        provider_id="com.example.admission",
        capability_id="com.example.admission",
        kind="ADMISSION",
        input_schema=object_schema({"outcome": STRING}),
        output_schema=OBJECT,
        config_schema=OBJECT,
    )
    async def admission(inputs: Context, config: Context) -> Context:
        return {"outcome": inputs["outcome"], "reason": "Host policy"}

    catalog = local_catalog()
    catalog.register(admission)
    graph = echo_graph()
    choice = graph.input("admit", STRING, required=False, default=Constant(value="DEFER"))
    graph.execution_policy = ExecutionPolicy(
        activation=Capability(executor_ref="MANUAL"),
        selection=Capability(executor_ref="EXPLICIT"),
        admission=AdmissionPolicy(
            operation=OperationRequirement(
                capability_id="com.example.admission", capability_version="1"
            ),
            inputs=[
                InputPort(name="outcome", schema=STRING, required=True, on_unavailable="BLOCK")
            ],
            bindings={"outcome": choice.source},
        ),
    )
    for outcome in ("DEFER", "SKIP", "RUN"):
        run = Relay(catalog=catalog).run_sync(graph, inputs={"x": 1, "admit": outcome})
        assert run.record.admission.outcome == outcome
        assert run.record.nodes[0].state == ("SUCCESS" if outcome == "RUN" else "NONEXECUTED")
    graph.execution_policy = graph.execution_policy.model_copy(
        update={"activation": Capability(executor_ref="unsupported")}
    )
    with pytest.raises(ProtocolError, match="POLICY_UNSUPPORTED"):
        Relay(catalog=catalog).run_sync(graph, inputs={"x": 1})


def test_observer_failure_store_snapshots_and_guardrail(tmp_path: Path) -> None:
    def broken(event: object) -> None:
        raise RuntimeError("secret diagnostic must not leak")

    store = JsonlStore(tmp_path / "records.jsonl")
    relay = Relay(store=store, observer=CallbackObserver(broken))
    run = relay.run_sync(text_graph(), inputs={"text": "Migration Rollback"})
    assert run.record.extensions[0].data != {}
    run.record.run_inputs["text"] = "mutated"
    retained = store.get(run.record.run_id)
    assert retained is not None and retained.run_inputs["text"] == "Migration Rollback"
    assert JsonlStore(store.path).get(run.record.run_id) == retained

    async def check() -> None:
        invoked: list[str] = []

        async def action() -> str:
            invoked.append("ran")
            return "done"

        inputs: Context = {
            "action": "delete",
            "target": "src/auth.py",
            "allowed_prefixes": ["tmp/"],
        }
        with pytest.raises(ProtocolError, match="GATE_REJECTED"):
            await relay.verify_before(action, guardrail_graph(), inputs=inputs)
        assert not invoked
        inputs["target"] = "tmp/disposable.txt"
        assert await relay.verify_before(action, guardrail_graph(), inputs=inputs) == "done"
        assert invoked == ["ran"]

    asyncio.run(check())
