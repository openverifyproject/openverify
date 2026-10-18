"""Missing explicit assertions for public forwarding and snapshot helpers."""

import ast
import hashlib
import inspect
import json

import pytest

from openverify import Graph, ProtocolError, fingerprint
from openverify.authoring import constant, external
from openverify.model import ArtifactRef, Constant, Criterion
from openverify.serialization import to_data

PARSERS = [
    ("VCP", "parse_definition", "verification-definition", "CM.SDK.PARSE.DEFINITION"),
    ("VCP", "parse_result", "result", "CM.SDK.PARSE.RESULT"),
    ("VCP", "parse_run_record", "run-record", "CM.SDK.PARSE.RECORD"),
    (
        "PROVIDER",
        "parse_provider_manifest",
        "provider-manifest",
        "CM.SDK.PROVIDER.PARSE_PROVIDER_MANIFEST",
    ),
    ("PROVIDER", "parse_invocation", "invocation", "CM.SDK.PROVIDER.PARSE_INVOCATION"),
    ("PROVIDER", "parse_provider_event", "provider-event", "CM.SDK.PROVIDER.PARSE_PROVIDER_EVENT"),
    ("PROVIDER", "parse_outcome", "outcome", "CM.SDK.PROVIDER.PARSE_OUTCOME"),
    ("PROVIDER", "parse_cancel_request", "cancel-request", "CM.SDK.PROVIDER.PARSE_CANCEL_REQUEST"),
]


@pytest.mark.parametrize("layer,name,root,requirement_id", PARSERS, ids=[r[1] for r in PARSERS])
@pytest.mark.parametrize("failure", [False, True], ids=["RETURN", "PROPAGATE"])
def test_public_parse_forwarding(layer, name, root, requirement_id, failure, monkeypatch, request):
    from openverify import validation
    from openverify.provider import validation as provider_validation

    module = validation if layer == "VCP" else provider_validation
    function = getattr(module, name)
    source = ast.parse(inspect.getsource(function)).body[0]
    # Mechanical universal premise: a single return expression, no conditional,
    # loop, handler or alternate path. Behavioral checks establish arguments,
    # unchanged result identity and unchanged exception identity.
    assert len(source.body) == 1 and isinstance(source.body[0], ast.Return)
    assert not any(isinstance(n, (ast.If, ast.Try, ast.For, ast.While)) for n in ast.walk(source))
    calls, raw, returned = [], {"independently": ["authored", None]}, object()
    error = ProtocolError("PROTOCOL_STRUCTURE", "authored rejection")

    def parse(kind, data):
        calls.append((kind, data))
        if failure:
            raise error
        return returned

    monkeypatch.setattr(
        module, "parse_object" if layer == "VCP" else "parse_provider_object", parse
    )
    request.node.canonical_ids = [requirement_id]
    if failure:
        with pytest.raises(ProtocolError) as caught:
            function(raw)
        assert caught.value is error
    else:
        assert function(raw) is returned
    assert calls == [(root, raw)]
    assert calls[0][1] is raw


def test_exact_fingerprint_and_error_data(request):
    definition = Graph("fingerprint").build()
    # Serialization contract is explicit here rather than using SUT serialization
    # to compute its own expected digest.
    raw = to_data(definition)
    encoded = json.dumps(
        raw, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode()
    assert fingerprint(definition) == "local-sha256:" + hashlib.sha256(encoded).hexdigest()
    error = ProtocolError("DATAFLOW_BINDING", "authored", "/x", {"value": None})
    assert error.as_dict() == {
        "code": "DATAFLOW_BINDING",
        "message": "authored",
        "path": "/x",
        "details": {"value": None},
    }
    from openverify.provider import ProviderContractError

    assert ProviderContractError("INVALID_INPUT", "authored", {"value": None}).as_dict() == {
        "code": "INVALID_INPUT",
        "message": "authored",
        "details": {"value": None},
    }
    request.node.canonical_ids = [
        "CM.SDK.FINGERPRINT",
        "CM.SDK.ERROR.ASDICT",
        "CM.SDK.PROVIDER.ERROR.ASDICT",
    ]


def test_authoring_sources_and_output_reference(request):
    ref = constant({"x": None}, {"type": "object"})
    assert to_data(ref.source) == {"kind": "CONSTANT", "value": {"x": None}}
    assert ref.schema == {"type": "object"}
    artifact = ArtifactRef(id="a", type="json", locator=None)
    assert to_data(external(artifact).source) == {
        "kind": "EXTERNAL_REFERENCE",
        "reference": {"id": "a", "type": "json", "locator": None},
    }
    graph = Graph("refs")
    n = graph.derive("n", "com.example.compute", outputs={"x": True})
    assert to_data(n["x"].source) == {"kind": "UPSTREAM_OUTPUT", "node_id": "n", "output": "x"}
    with pytest.raises(KeyError):
        n["missing"]
    request.node.canonical_ids = [
        "CM.SDK.REFERENCE.CONSTANT",
        "CM.SDK.REFERENCE.EXTERNAL",
        "CM.SDK.NODE.OUTPUT",
    ]


@pytest.mark.parametrize("kind", ["DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"])
def test_authored_kind_roles_and_snapshot(kind, request):
    graph = Graph(
        "authored",
        subject=ArtifactRef(id="s", type="json", locator={"x": 17}),
        criterion=Criterion(id="c", description="authored criterion"),
    )
    config, schema = {"nested": {"x": 17}}, {"type": "object"}
    inputs = {"x": constant({"a": None}, schema)}
    if kind == "AGGREGATE":
        graph.aggregate("n", {}, capability="com.example.custom", config=config)
    else:
        graph.node(
            "n",
            kind,
            "com.example.compute",
            version="v",
            inputs=inputs,
            outputs={"info": True},
            config=config,
            config_schema=True,
        )
    config["nested"]["x"] = 29
    built = graph.build()
    authored = built.graph.nodes[0]
    assert authored.kind == kind
    assert authored.operation.capability_id == (
        "com.example.custom" if kind == "AGGREGATE" else "com.example.compute"
    )
    assert authored.config == {"nested": {"x": 17}}
    roles = {p.name: p.role for p in authored.outputs}
    if kind == "DERIVE":
        assert roles == {"info": "INFORMATION"}
    elif kind == "CONTROL":
        assert roles == {"info": "INFORMATION", "decision": "DECISION"}
    else:
        assert roles == (
            {"result": "RESULT"}
            if kind == "AGGREGATE"
            else {"info": "INFORMATION", "result": "RESULT"}
        )
        assert authored.bindings["subject"].value == {
            "id": "s",
            "type": "json",
            "locator": {"x": 17},
        }
        assert authored.bindings["criterion"].value == {
            "id": "c",
            "description": "authored criterion",
        }
    request.node.canonical_ids = [
        "CM.SDK.AUTHORING.GRAPH.NODE.OPERATION",
        "CM.SDK.AUTHORING.GRAPH.NODE.CONFIG_SNAPSHOT",
        "CM.SDK.AUTHORING.GRAPH.NODE.OUTPUTS",
    ] + (
        ["CM.SDK.AUTHORING.GRAPH.NODE.SEMANTIC_INPUTS"] if kind in ("EVALUATE", "AGGREGATE") else []
    )


@pytest.mark.parametrize(
    "required,default,handler",
    [(True, None, "BLOCK"), (False, None, "OMIT"), (False, Constant(value=None), "DEFAULT")],
    ids=["REQUIRED", "OPTIONAL", "DEFAULT_NULL"],
)
def test_authored_run_input(required, default, handler, request):
    graph = Graph("inputs")
    schema = {"type": ["integer", "null"]}
    ref = graph.input("x", schema, required=required, default=default)
    schema["type"].append("string")
    p = graph.build().run_inputs[0]
    assert p.value_schema == {"type": ["integer", "null"]}
    assert p.required == required and p.on_unavailable == handler
    assert to_data(ref.source) == {"kind": "RUN_INPUT", "name": "x"}
    assert ref.schema == {"type": ["integer", "null"]}
    if default is not None:
        assert p.default.value is None
    request.node.canonical_ids = [
        "CM.SDK.AUTHORING.GRAPH.INPUT.PORT",
        "CM.SDK.AUTHORING.GRAPH.INPUT.REF",
    ]


def test_lifecycle_manifest_snapshot_is_independent(request):
    from openverify.provider import LifecycleValidator, parse_provider_manifest
    from tests.unit.test_provider_contract import invocation_data, manifest_data

    manifest = parse_provider_manifest(manifest_data())
    lifecycle = LifecycleValidator(manifest)
    manifest.capabilities.clear()
    assert (
        lifecycle.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})
        == "0.1"
    )
    assert lifecycle.accept(invocation_data()) is None
    assert (
        lifecycle.outcome({"invocation_id": "attempt-1", "state": "COMPLETED", "output": "hello"})
        is None
    )
    assert lifecycle.finish() is None
    request.node.canonical_ids = [
        "CM.SDK.PROVIDER.LIFECYCLE.MANIFEST",
        "CM.PROVIDER.MANIFEST.SNAPSHOT",
    ]
