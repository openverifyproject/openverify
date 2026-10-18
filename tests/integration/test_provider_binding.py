"""The host chooses concrete providers; the engine enforces their contracts."""

from copy import deepcopy

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import JsonValue

from openverify import ProtocolError, parse_run_record, serialize
from openverify.adapters import Registry
from openverify.adapters.demo import known
from openverify.engine import Engine
from openverify.engine.binding import BoundProvider
from openverify.lifecycle import Cancellation
from openverify.model import (
    Constant,
    Context,
    Edge,
    ExecutionError,
    ExecutionObservation,
    Graph,
    InputPort,
    JsonSchema,
    Measurement,
    ProviderBinding,
    RunRecord,
    UpstreamOutput,
    VerificationDefinition,
)
from openverify.provider.model import Capability, LifecycleFeatures, ProviderManifest
from openverify.serialization import to_data
from tests.dataflow_helpers import Echo, Judge, derive, flow, input_port
from tests.helpers import definition, handling, node


class Spy:
    def __init__(self, output: ExecutionObservation | None = None) -> None:
        self.calls: list[tuple[Context, Context]] = []
        self.output = output

    def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
        self.calls.append((deepcopy(inputs), deepcopy(config)))
        return self.output or ExecutionObservation(outputs={"x": inputs["x"]})


def bound(
    adapter: Spy | Echo | Judge,
    *,
    provider_id: str = "com.example.provider",
    capability_id: str = "com.example.echo",
    input_schema: JsonSchema = True,
    config_schema: JsonSchema = True,
    output_schema: JsonSchema = True,
) -> BoundProvider:
    capability = Capability(
        capability_id=capability_id,
        capability_version="1",
        input_schema=input_schema,
        config_schema=config_schema,
        output_schema=output_schema,
        vcp_version="draft",
        lifecycle_features=LifecycleFeatures(
            streaming=False, cancellation=True, deadlines=False, resource_reporting=True
        ),
    )
    manifest = ProviderManifest(
        provider_id=provider_id,
        provider_version="release-7",
        supported_contract_versions=["0.1"],
        supported_vcp_versions=["draft"],
        capabilities=[capability],
    )
    return BoundProvider(
        ProviderBinding(
            provider_id=manifest.provider_id,
            provider_version=manifest.provider_version,
            capability_id=capability.capability_id,
            capability_version=capability.capability_version,
        ),
        manifest,
        adapter,
    )


def single(schema: JsonSchema = True, *, config: Context | None = None) -> VerificationDefinition:
    producer = derive("producer", schema=schema).model_copy(update={"config": config or {}})
    return definition("generic").model_copy(
        update={"run_inputs": [input_port("x", schema)], "graph": Graph(nodes=[producer])}
    )


def run(provider: BoundProvider, value: JsonValue = "hello") -> RunRecord:
    return Engine(Registry(), provider_bindings={"producer": provider}).run(
        single(), {"x": value}, opportunity_id="bound"
    )


def test_exact_bound_input_config_output_and_provenance() -> None:
    spy = Spy()
    schema: JsonSchema = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "required": ["x"],
        "additionalProperties": False,
    }
    provider = bound(spy, input_schema=schema, output_schema=schema)
    record = Engine(Registry(), provider_bindings={"producer": provider}).run(
        single(config={"limit": 3}), {"x": "hello"}, opportunity_id="exact"
    )
    assert spy.calls == [({"x": "hello"}, {"limit": 3})]
    assert record.nodes[0].information == {"x": "hello"}
    assert record.provider_bindings == {"producer": provider.binding}
    assert record.nodes[0].provider_binding == provider.binding
    assert record.nodes[0].executor_ref == provider.binding.provider_id
    assert record.nodes[0].executor_version == provider.binding.provider_version
    assert parse_run_record(serialize(record)) == record


@pytest.mark.parametrize("value", [42, False, None, [], {}])
def test_provider_input_rejects_values_accepted_by_vcp(value: JsonValue) -> None:
    spy = Spy()
    record = run(bound(spy, input_schema={"properties": {"x": {"type": "string"}}}), value)
    node = record.nodes[0]
    assert node.input_values == {"x": value}
    assert node.reason == "INVALID_INPUT"
    assert node.state == "ERROR"
    assert node.result is not None and isinstance(node.result.output, dict)
    assert node.result.output["code"] == "INVALID_INPUT"
    assert not spy.calls and node.observation is None
    assert not record.provider_bindings and node.provider_binding is None


def test_narrower_provider_input_contract_remains_distinct_from_vcp() -> None:
    spy = Spy()
    record = Engine(
        Registry(),
        provider_bindings={
            "producer": bound(spy, input_schema={"properties": {"x": {"maxLength": 3}}})
        },
    ).run(single({"type": "string"}), {"x": "longer"}, opportunity_id="narrow")
    assert record.nodes[0].reason == "INVALID_INPUT"
    assert not spy.calls


def test_provider_receives_exact_resolved_defaults_and_omissions() -> None:
    d = single()
    producer = d.graph.nodes[0]
    producer.inputs.extend(
        [
            InputPort(
                name="defaulted",
                schema=True,
                required=False,
                on_unavailable="DEFAULT",
                default=Constant(value=None),
            ),
            input_port("omitted", required=False),
        ]
    )
    spy = Spy()
    schema: JsonSchema = {
        "type": "object",
        "properties": {"x": True, "defaulted": {"type": "null"}},
        "required": ["x", "defaulted"],
        "additionalProperties": False,
    }
    record = Engine(
        Registry(), provider_bindings={"producer": bound(spy, input_schema=schema)}
    ).run(d, {"x": "hello"}, opportunity_id="resolution")
    assert spy.calls == [({"x": "hello", "defaulted": None}, {})]
    assert record.nodes[0].state == "SUCCESS"


def test_provider_contract_local_refs_and_json_type_equality() -> None:
    schema: JsonSchema = {
        "$defs": {"value": {"const": 0}},
        "properties": {"x": {"$ref": "#/$defs/value"}},
    }
    spy = Spy()
    assert run(bound(spy, input_schema=schema), 0).nodes[0].state == "SUCCESS"
    assert run(bound(spy, input_schema=schema), False).nodes[0].reason == "INVALID_INPUT"
    assert len(spy.calls) == 1


def test_provider_configuration_is_checked_before_invocation() -> None:
    spy = Spy()
    provider = bound(spy, config_schema={"required": ["limit"]})
    record = run(provider)
    assert record.nodes[0].reason == "INVALID_CONFIG"
    assert not spy.calls
    valid = Engine(Registry(), provider_bindings={"producer": provider}).run(
        single(config={"limit": 1}), {"x": "hello"}, opportunity_id="config"
    )
    assert valid.nodes[0].state == "SUCCESS" and len(spy.calls) == 1


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("capability_id", "PROVIDER_BINDING_MISMATCH"),
        ("capability_version", "PROVIDER_BINDING_MISMATCH"),
        ("provider_id", "PROVIDER_BINDING_MISMATCH"),
        ("provider_version", "PROVIDER_BINDING_MISMATCH"),
        ("missing_capability", "CAPABILITY_UNAVAILABLE"),
        ("missing_version", "CAPABILITY_VERSION_UNSUPPORTED"),
        ("bad_input_schema", "PROVIDER_MANIFEST_INVALID"),
        ("bad_output_schema", "PROVIDER_MANIFEST_INVALID"),
        ("bad_config_schema", "PROVIDER_MANIFEST_INVALID"),
        ("external_schema", "PROVIDER_MANIFEST_INVALID"),
        ("duplicate_capability", "PROVIDER_MANIFEST_INVALID"),
        ("contract", "CONTRACT_VERSION_UNSUPPORTED"),
        ("vcp", "INVALID_INVOCATION"),
    ],
)
def test_binding_validation_prevents_invocation(mutation: str, code: str) -> None:
    spy = Spy()
    provider = bound(spy)
    manifest = provider.manifest
    capability = manifest.capabilities[0]
    if mutation in ("capability_id", "provider_id"):
        provider = BoundProvider(
            provider.binding.model_copy(update={mutation: "com.example.other"}), manifest, spy
        )
    elif mutation in ("capability_version", "provider_version"):
        provider = BoundProvider(provider.binding.model_copy(update={mutation: "2"}), manifest, spy)
    elif mutation == "missing_capability":
        manifest.capabilities.clear()
    elif mutation == "missing_version":
        manifest.capabilities[0] = capability.model_copy(update={"capability_version": "2"})
    elif mutation.startswith("bad_"):
        manifest.capabilities[0] = capability.model_copy(
            update={mutation.removeprefix("bad_"): {"type": "bogus"}}
        )
    elif mutation == "external_schema":
        manifest.capabilities[0] = capability.model_copy(
            update={"input_schema": {"$ref": "https://example.invalid/schema"}}
        )
    elif mutation == "duplicate_capability":
        manifest.capabilities.append(capability)
    elif mutation == "contract":
        manifest.supported_contract_versions[:] = ["future"]
    else:
        manifest.capabilities[0] = capability.model_copy(update={"vcp_version": "future"})
        manifest.supported_vcp_versions[:] = ["future"]
    record = run(provider)
    assert record.nodes[0].reason == code
    assert not spy.calls
    assert not record.provider_bindings


def test_two_compatible_providers_require_explicit_host_binding() -> None:
    first, second = Spy(), Spy()
    providers = [bound(first), bound(second, provider_id="com.example.second")]
    local = Registry()
    local.register("com.example.echo", "1", first)
    record = Engine(local, provider_bindings={}).run(
        single(), {"x": "hello"}, opportunity_id="unbound"
    )
    assert record.nodes[0].reason == "PROVIDER_BINDING_REQUIRED"
    assert not first.calls and not second.calls
    selected = run(providers[1])
    assert selected.nodes[0].provider_binding == providers[1].binding
    assert not first.calls and len(second.calls) == 1


def test_explicit_mode_never_falls_back_to_builtin_aggregate() -> None:
    aggregate = node(
        id="aggregate",
        kind="AGGREGATE",
        executor_ref="standard.aggregate",
        config={"reducer": "ALL", "handling": handling()},
    )
    judge = node(id="judge", kind="EVALUATE", executor_ref="judge")
    aggregate.inputs.append(input_port("member", {"type": "object"}))
    aggregate.bindings["member"] = UpstreamOutput(node_id="judge", output="result")
    aggregate.bindings["members"] = Constant(value=["member"])
    aggregate = aggregate.model_copy(update={"aggregate_inputs": ["member"]})
    d = definition("generic").model_copy(
        update={
            "graph": Graph(
                nodes=[judge, aggregate], edges=[Edge(from_node="judge", to_node="aggregate")]
            ),
            "run_inputs": [],
        }
    )
    record = Engine(Registry(), provider_bindings={}).run(d, {}, opportunity_id="builtin")
    assert record.nodes[1].reason == "PROVIDER_BINDING_REQUIRED"
    spy = Spy(ExecutionObservation(outputs={"result": {}}))
    provider = bound(spy, capability_id="openverify.aggregate", input_schema=False)
    judge_provider = bound(
        Spy(ExecutionObservation(outputs={"result": to_data(known("PASS"))})),
        capability_id="com.example.judge",
    )
    record = Engine(
        Registry(), provider_bindings={"judge": judge_provider, "aggregate": provider}
    ).run(d, {}, opportunity_id="override")
    assert record.nodes[1].reason == "INVALID_INPUT"
    assert not spy.calls


def test_vcp_interchange_is_required_for_bound_result_capabilities() -> None:
    producer = bound(Echo())
    judge = bound(Judge(), capability_id="com.example.echo.judge")
    judge.manifest.capabilities[0] = judge.manifest.capabilities[0].model_copy(
        update={"vcp_version": None}
    )
    # The optional Provider Contract field must be absent, rather than explicit null.
    capability = judge.manifest.capabilities[0]
    judge.manifest.capabilities[0] = Capability(
        capability_id=capability.capability_id,
        capability_version=capability.capability_version,
        input_schema=True,
        output_schema=True,
        config_schema=True,
        lifecycle_features=capability.lifecycle_features,
    )
    record = Engine(Registry(), provider_bindings={"producer": producer, "consumer": judge}).run(
        flow(), {"x": "hello"}, opportunity_id="vcp"
    )
    assert record.nodes[1].reason == "INVALID_INVOCATION"
    assert record.nodes[1].provider_binding is None


@pytest.mark.parametrize("where", ["node", "invocation"])
def test_deleting_one_binding_snapshot_is_rejected(where: str) -> None:
    record = run(bound(Spy()))
    if where == "node":
        record.nodes[0] = record.nodes[0].model_copy(update={"provider_binding": None})
    else:
        record.provider_bindings.clear()
    with pytest.raises(ProtocolError) as exc:
        parse_run_record(serialize(record))
    assert exc.value.code == "PROVENANCE_LINEAGE"


@pytest.mark.parametrize(
    "field", ["provider_id", "provider_version", "capability_id", "capability_version"]
)
@pytest.mark.parametrize("where", ["node", "invocation", "executor"])
def test_provider_identity_mutations_are_rejected(field: str, where: str) -> None:
    record = run(bound(Spy()))
    if where == "node":
        assert record.nodes[0].provider_binding is not None
        changed = record.nodes[0].provider_binding.model_copy(update={field: "com.example.changed"})
        record.nodes[0] = record.nodes[0].model_copy(update={"provider_binding": changed})
    elif where == "invocation":
        record.provider_bindings["producer"] = record.provider_bindings["producer"].model_copy(
            update={field: "com.example.changed"}
        )
    else:
        name = "executor_version" if field.endswith("version") else "executor_ref"
        record.nodes[0] = record.nodes[0].model_copy(update={name: "com.example.changed"})
    with pytest.raises(ProtocolError) as exc:
        parse_run_record(serialize(record))
    assert exc.value.code == "PROVENANCE_LINEAGE"


@given(version=st.text(alphabet="0123456789abcdef", min_size=1, max_size=16))
def test_any_substituted_provider_version_is_rejected(version: str) -> None:
    record = run(bound(Spy()))
    binding = record.nodes[0].provider_binding
    assert binding is not None
    record.nodes[0] = record.nodes[0].model_copy(
        update={"provider_binding": binding.model_copy(update={"provider_version": version})}
    )
    with pytest.raises(ProtocolError) as exc:
        parse_run_record(serialize(record))
    assert exc.value.code == "PROVENANCE_LINEAGE"


def test_coordinated_capability_rewrite_still_must_satisfy_node_requirement() -> None:
    record = run(bound(Spy()))
    wrong = record.provider_bindings["producer"].model_copy(
        update={"capability_id": "com.example.other"}
    )
    record.provider_bindings["producer"] = wrong
    record.nodes[0] = record.nodes[0].model_copy(update={"provider_binding": wrong})
    with pytest.raises(ProtocolError) as exc:
        parse_run_record(serialize(record))
    assert exc.value.code == "PROVENANCE_LINEAGE"


def test_invalid_provider_output_retains_usage_and_cannot_feed_downstream() -> None:
    usage = {"tokens": Measurement(unit="token", kind="EXACT", value=4)}
    raw = ExecutionObservation(outputs={"x": 17}, usage=usage)
    producer = Spy(raw)
    consumer = Spy()
    record = Engine(
        Registry(),
        provider_bindings={
            "producer": bound(producer, output_schema={"properties": {"x": {"type": "string"}}}),
            "consumer": bound(consumer, capability_id="com.example.echo.judge"),
        },
    ).run(flow(), {"x": "valid"}, opportunity_id="rejected-output")
    node, downstream = record.nodes
    assert len(producer.calls) == 1 and not consumer.calls
    assert node.reason == "INVALID_PROVIDER_OUTPUT" and node.state == "ERROR"
    assert node.observation == raw
    assert node.observation is not None
    assert node.observation.usage == usage
    assert node.provider_output_error is not None
    assert not node.information and node.decision is None
    assert downstream.reason == "INPUT_UNAVAILABLE"
    assert downstream.input_resolutions["x"].status == "INVALID"
    assert "x" not in downstream.input_values
    assert downstream.provider_binding is None
    assert parse_run_record(serialize(record)) == record
    record.nodes[0] = node.model_copy(update={"information": {"x": 17}})
    with pytest.raises(ProtocolError) as exc:
        parse_run_record(serialize(record))
    assert exc.value.code == "PROVENANCE_LINEAGE"


def test_vcp_semantic_boundary_still_rejects_contract_valid_output() -> None:
    record = run(bound(Spy(ExecutionObservation(outputs={"wrong_port": 1}))))
    assert record.nodes[0].reason == "OUTPUT_MISSING"
    assert record.nodes[0].provider_output_error is None
    assert not record.nodes[0].information


def test_provider_error_observation_has_no_successful_output_contract() -> None:
    raw = ExecutionObservation(
        error=ExecutionError(code="com.example.failed", message="failed"),
        usage={"tokens": Measurement(unit="token", kind="EXACT", value=4)},
    )
    record = run(bound(Spy(raw), output_schema=False))
    assert record.nodes[0].reason == "com.example.failed"
    assert record.nodes[0].observation == raw
    assert record.nodes[0].provider_output_error is None
    assert record.nodes[0].provider_binding is not None


def test_provider_that_raises_still_records_invocation_binding() -> None:
    class Raises(Spy):
        def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
            raise RuntimeError("failed")

    provider = bound(Raises())
    record = run(provider)
    assert record.nodes[0].reason == "EXECUTOR_ERROR"
    assert record.nodes[0].provider_binding == provider.binding
    assert record.provider_bindings == {"producer": provider.binding}


def test_host_bindings_are_snapshotted_before_provider_code_runs() -> None:
    class Mutates(Spy):
        def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
            provider.manifest.capabilities.clear()
            inputs["x"] = "mutated"
            config["changed"] = True
            return ExecutionObservation(outputs={"x": "invalid"})

    provider = bound(Mutates(), output_schema={"properties": {"x": {"const": "hello"}}})
    record = run(provider)
    assert record.nodes[0].reason == "INVALID_PROVIDER_OUTPUT"
    assert record.nodes[0].input_values == {"x": "hello"}
    assert record.definition.graph.nodes[0].config == {}


def test_cancelled_provider_invocation_retains_binding_and_unaccepted_usage() -> None:
    cancellation = Cancellation()

    class Cancels(Spy):
        def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
            cancellation.cancel("host cancelled")
            return ExecutionObservation(
                outputs={"x": 17},
                usage={"tokens": Measurement(unit="token", kind="EXACT", value=4)},
            )

    provider = bound(Cancels(), output_schema=False)
    record = Engine(Registry(), provider_bindings={"producer": provider}).run(
        single(), {"x": "hello"}, opportunity_id="cancel", cancellation=cancellation
    )
    assert record.nodes[0].state == "CANCELLED"
    assert record.nodes[0].provider_binding == provider.binding
    assert record.nodes[0].observation is not None and record.nodes[0].observation.usage
    assert not record.nodes[0].information
    assert parse_run_record(serialize(record)) == record
