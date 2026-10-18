"""Previously unlinked public boundaries, with exact authored outcomes."""

import asyncio

import pytest

from openverify import Graph, Relay, parse_run_record
from openverify.model import Activation, Admission, Decision, Result, Selection
from openverify.provider import Invocation, wire_data
from openverify.relay import RuntimeConfig, provider
from openverify.relay.entrypoints.service import GraphService
from openverify.serialization import to_data


def decorate(kind):
    return provider(
        provider_id="com.example.wrapper",
        capability_id="com.example.compute",
        kind=kind,
        input_schema=True,
        output_schema=True,
        config_schema=True,
    )


@pytest.mark.parametrize(
    "kind", ["DERIVE", "EVALUATE", "AGGREGATE", "CONTROL", "ACTIVATION", "SELECTION", "ADMISSION"]
)
def test_function_provider_normalization_and_manifest(kind, request):
    authored = {
        "DERIVE": ({"x": 17}, {"x": 17}),
        "EVALUATE": (
            Result(disposition="EXECUTED", execution_outcome="ERROR"),
            {
                "result": {
                    "protocol": "draft",
                    "disposition": "EXECUTED",
                    "execution_outcome": "ERROR",
                    "evidence": [],
                    "usage": {},
                }
            },
        ),
        "AGGREGATE": (
            Result(disposition="EXECUTED", execution_outcome="ERROR"),
            {
                "result": {
                    "protocol": "draft",
                    "disposition": "EXECUTED",
                    "execution_outcome": "ERROR",
                    "evidence": [],
                    "usage": {},
                }
            },
        ),
        "CONTROL": (
            Decision(kind="CONTINUE"),
            {"decision": {"protocol": "draft", "kind": "CONTINUE"}},
        ),
        "ACTIVATION": (
            Activation(outcome="ACTIVATE", reason="authored"),
            {"outcome": "ACTIVATE", "reason": "authored"},
        ),
        "SELECTION": (
            Selection(subjects=[], reason="authored"),
            {"subjects": [], "reason": "authored"},
        ),
        "ADMISSION": (
            Admission(outcome="RUN", reason="authored"),
            {"outcome": "RUN", "reason": "authored"},
        ),
    }
    sent, expected = authored[kind]
    calls = []

    @decorate(kind)
    async def implementation(inputs, config):
        calls.append((inputs, config))
        return sent

    manifest = wire_data(implementation.manifest())
    assert manifest["provider_id"] == "com.example.wrapper"
    assert manifest["supported_contract_versions"] == ["0.1"]
    assert manifest["supported_vcp_versions"] == ["draft"]
    capability = manifest["capabilities"][0]
    assert capability["lifecycle_features"] == {
        "streaming": True,
        "cancellation": True,
        "deadlines": False,
        "resource_reporting": True,
    }
    assert capability["extensions"] == {"openverify.operation": {"kind": kind}}
    invocation = Invocation(
        invocation_id="a",
        contract_version="0.1",
        capability_id="com.example.compute",
        capability_version="1",
        vcp_version="draft",
        input={"x": 17},
        config={"y": 29},
    )

    async def run():
        return [wire_data(item) async for item in implementation.invoke(invocation)]

    actual = asyncio.run(run())
    assert actual == [
        {"invocation_id": "a", "state": "COMPLETED", "output": expected, "resource_usage": {}}
    ]
    assert calls == [({"x": 17}, {"y": 29})]
    request.node.canonical_ids = [
        "CM.SDK.FUNCTION_PROVIDER.MANIFEST",
        "CM.SDK.PROVIDER.INTERFACE.MANIFEST",
        "CM.SDK.PROVIDER.INTERFACE.INVOKE",
    ] + (
        ["CM.SDK.FUNCTION_PROVIDER.RESULT"]
        if kind in ("EVALUATE", "AGGREGATE")
        else ["CM.SDK.FUNCTION_PROVIDER.DECISION"]
        if kind == "CONTROL"
        else ["CM.SDK.FUNCTION_PROVIDER.POLICY"]
        if kind in ("ACTIVATION", "SELECTION", "ADMISSION")
        else []
    )


def test_function_provider_exception_and_async_requirement(request):
    with pytest.raises(TypeError, match="must be async"):
        decorate("DERIVE")(lambda inputs, config: {})

    @decorate("DERIVE")
    async def failure(inputs, config):
        raise ValueError("authored failure")

    invocation = Invocation(
        invocation_id="a",
        contract_version="0.1",
        capability_id="com.example.compute",
        capability_version="1",
        vcp_version="draft",
        input={},
        config={},
    )

    async def run():
        return [wire_data(item) async for item in failure.invoke(invocation)]

    assert asyncio.run(run()) == [
        {
            "invocation_id": "a",
            "state": "ERROR",
            "error": {"code": "openverify.computation_error", "message": "authored failure"},
        }
    ]
    request.node.canonical_ids = [
        "CM.SDK.FUNCTION_PROVIDER.ASYNC",
        "CM.SDK.FUNCTION_PROVIDER.EXCEPTION",
    ]


@pytest.mark.parametrize("concurrency", [0, -1, True, 1.5])
def test_runtime_config_rejects_nonpositive_noninteger_concurrency(concurrency, request):
    with pytest.raises(ValueError, match="positive integer"):
        RuntimeConfig(max_concurrency=concurrency)
    request.node.canonical_ids = ["CM.SDK.RELAY.CONFIG"]


@pytest.mark.parametrize(
    "timeout", [0, -1, float("inf"), float("nan")], ids=["ZERO", "NEGATIVE", "INFINITY", "NAN"]
)
def test_runtime_config_rejects_invalid_timeout(timeout, request):
    with pytest.raises(ValueError, match="finite and positive"):
        RuntimeConfig(timeout=timeout)
    request.node.canonical_ids = ["CM.SDK.RELAY.CONFIG"]


def test_service_authorization_snapshots_and_record_operations(request):
    from openverify.relay.errors import RelayError

    service = GraphService(graphs={"z": Graph("z"), "a": Graph("a")})
    assert service.list_graphs() == ["a", "z"]
    definition = service.definition("a")
    definition.graph.nodes.clear()
    assert service.definition("a").id == "a"
    assert service.describe_graph("a")["id"] == "a"
    with pytest.raises(RelayError, match="GRAPH_UNAVAILABLE"):
        service.definition("not-authorized")
    with pytest.raises(RelayError, match="RUN_UNAVAILABLE"):
        service.inspect_result("not-retained")
    wire = asyncio.run(service.run_graph("a", {}))
    assert wire["definition"]["id"] == "a"
    assert wire["final_results"] == {}
    assert service.inspect_result(wire["run_id"]) == wire
    assert parse_run_record(wire).definition.id == "a"
    request.node.canonical_ids = [
        "CM.SDK.SERVICE.GRAPHSERVICE.DEFINITION",
        "CM.SDK.SERVICE.GRAPHSERVICE.DESCRIBE_GRAPH",
        "CM.SDK.SERVICE.GRAPHSERVICE.LIST_GRAPHS",
        "CM.SDK.SERVICE.GRAPHSERVICE.INSPECT_RESULT",
        "CM.SDK.SERVICE.GRAPHSERVICE.RUN_GRAPH.AUTHORIZATION",
        "CM.SDK.SERVICE.GRAPHSERVICE.RUN_GRAPH.RESULT",
    ]


def test_run_views_and_serialization_match_authored_single_node_record(request):
    from openverify.relay.adapters.catalog import Catalog

    @decorate("CONTROL")
    async def continuation(inputs, config):
        return Decision(kind="CONTINUE")

    catalog = Catalog()
    catalog.register(continuation)
    graph = Graph("views")
    graph.control("c", "com.example.compute")
    run = Relay(catalog=catalog).run_sync(graph, inputs={})
    assert set(run.results) == set(run.record.final_results) == set()
    assert {k: to_data(v) for k, v in run.decisions.items()} == {
        "c": {"protocol": "draft", "kind": "CONTINUE"}
    }
    assert run.evidence == {"c": []}
    assert run.usage["c"]["wall_time"].unit == "s"
    assert parse_run_record(run.to_json()) == run.record
    request.node.canonical_ids = [
        "CM.RELAY.API.VIEWS.RESULTS",
        "CM.RELAY.API.VIEWS.DECISIONS",
        "CM.RELAY.API.VIEWS.EVIDENCE",
        "CM.RELAY.API.VIEWS.USAGE",
        "CM.RELAY.API.VIEWS.SERIALIZATION",
        "CM.SDK.RELAY.RUN_SYNC",
    ]


def test_custom_empty_membership_obeys_capability_input_schema(request):
    from openverify import parse_definition
    from openverify.relay.adapters.catalog import Catalog

    from .test_snapshot import OP, custom_definition

    calls = []

    @provider(
        provider_id="com.example.empty",
        capability_id=OP["capability_id"],
        kind="AGGREGATE",
        input_schema={"type": "object", "properties": {"members": {"minItems": 1}}},
        output_schema=True,
        config_schema=True,
    )
    async def implementation(inputs, config):
        calls.append(inputs)
        return Result(disposition="EXECUTED", execution_outcome="ERROR")

    catalog = Catalog()
    catalog.register(implementation)
    run = Relay(catalog=catalog).run_sync(parse_definition(custom_definition()), inputs={})
    record = run.record.nodes[0]
    assert calls == []
    assert record.reason == "INVALID_INPUT"
    assert record.input_values["members"] == []
    assert record.input_resolutions["members"].status == "AVAILABLE"
    assert record.provider_binding is None
    request.node.canonical_ids = ["CM.VCP.BIND.INPUT", "CM.VCP.AGG.MEMBERS_INPUT.CONSTANT"]


def test_unavailable_declared_member_never_becomes_empty_membership(request):
    from copy import deepcopy

    from openverify import parse_definition
    from openverify.relay.adapters.catalog import Catalog

    from .test_snapshot import OP, custom_definition, node, port

    definition = custom_definition()
    aggregate = definition["graph"]["nodes"][0]
    aggregate["aggregate_inputs"] = ["r"]
    aggregate["bindings"]["members"]["value"] = ["r"]
    aggregate["inputs"].append(port("r"))
    aggregate["bindings"]["r"] = {"kind": "UPSTREAM_OUTPUT", "node_id": "p", "output": "result"}
    producer = deepcopy(aggregate)
    producer.update(id="p", kind="EVALUATE", aggregate_inputs=[])
    producer["inputs"] = [p for p in producer["inputs"] if p["name"] in ("subject", "criterion")]
    producer["bindings"] = {
        k: v for k, v in producer["bindings"].items() if k in ("subject", "criterion")
    }
    producer["outputs"][0]["schema"] = {"type": "object", "required": ["verdict"]}
    producer["operation"]["capability_id"] = "com.example.evaluate"
    root = node("root")
    root["operation"] = {"capability_id": "com.example.root", "capability_version": "1"}
    definition["graph"] = {
        "nodes": [root, producer, aggregate],
        "edges": [
            {
                "from_node": "root",
                "to_node": "p",
                "guard": {
                    "source": {"kind": "CONSTANT", "value": False},
                    "pointer": "",
                    "value": True,
                },
            },
            {"from_node": "p", "to_node": "custom"},
        ],
    }
    calls = []

    @provider(
        provider_id="com.example.root",
        capability_id="com.example.root",
        kind="DERIVE",
        input_schema=True,
        output_schema=True,
        config_schema=True,
    )
    async def root_provider(inputs, config):
        calls.append("root")
        return {}

    async def compute(inputs, config):
        calls.append("computation")
        return Result(disposition="EXECUTED", execution_outcome="ERROR")

    catalog = Catalog()
    catalog.register(root_provider)
    for kind, capability in [
        ("EVALUATE", "com.example.evaluate"),
        ("AGGREGATE", OP["capability_id"]),
    ]:
        catalog.register(
            provider(
                provider_id=capability,
                capability_id=capability,
                kind=kind,
                input_schema=True,
                output_schema=True,
                config_schema=True,
            )(compute)
        )
    run = Relay(catalog=catalog).run_sync(parse_definition(definition), inputs={})
    record = run.record.nodes[-1]
    assert calls == ["root"]
    assert record.state == "NONEXECUTED" and record.reason == "INPUT_UNAVAILABLE"
    assert record.input_resolutions["r"].status == "INVALID"
    assert "r" not in record.input_values
    assert record.input_values["members"] == ["r"]
    assert run.record.definition.graph.nodes[-1].aggregate_inputs == ["r"]
    request.node.canonical_ids = [
        "CM.VCP.AGG.MEMBER_STATES",
        "CM.VCP.DATA.RESOLVE_BLOCK.NONINVOCATION",
    ]
