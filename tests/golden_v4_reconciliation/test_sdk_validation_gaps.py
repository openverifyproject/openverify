"""Explicit public validator results, serializer bytes and unknown-root errors."""

import pytest

from openverify import Graph, ProtocolError
from openverify import validation as vcp
from openverify.model import Result
from openverify.provider import ProviderContractError
from openverify.provider import validation as pc
from tests.unit.test_provider_contract import invocation_data, manifest_data


@pytest.mark.parametrize(
    "name", ["DEFINITION", "RESULT", "INVOCATION", "OUTCOME", "PROVIDER_EVENT", "PROVIDER_MANIFEST"]
)
@pytest.mark.parametrize("valid", [True, False], ids=["VALID", "INVALID"])
def test_public_validator_return_and_rejection(name, valid, request):
    if name == "DEFINITION":
        value = Graph("validator").build()
        invalid = value.model_copy(update={"version": ""})
        function, error, code = vcp.validate_definition, ProtocolError, "PROTOCOL_STRUCTURE"
        canonical = "CM.SDK.VALIDATE.DEFINITION"
    elif name == "RESULT":
        value = Result(disposition="SKIPPED")
        invalid = value.model_copy(update={"verdict": "PASS"})
        function, error, code = vcp.validate_result, ProtocolError, "RESULT_STATE"
        canonical = "CM.SDK.VALIDATE.RESULT"
    else:
        canonical = "CM.SDK.PROVIDER.VALIDATE_" + name
        error = ProviderContractError
        code = "INVALID_PROVIDER_OUTPUT"
        if name == "INVOCATION":
            value = pc.parse_invocation(invocation_data())
            invalid = value.model_copy(update={"contract_version": "0.2"})
            code = "CONTRACT_VERSION_UNSUPPORTED"
        elif name == "OUTCOME":
            value = pc.parse_outcome({"invocation_id": "a", "state": "COMPLETED", "output": None})
            invalid = value.model_copy(update={"state": "ERROR"})
        elif name == "PROVIDER_EVENT":
            value = pc.parse_provider_event(
                {"invocation_id": "a", "kind": "progress", "sequence": 1, "payload": None}
            )
            invalid = value.model_copy(update={"sequence": 0})
        else:
            value = pc.parse_provider_manifest(manifest_data())
            invalid = value.model_copy(
                update={"capabilities": [value.capabilities[0], value.capabilities[0]]}
            )
        function = getattr(pc, "validate_" + name.lower())
    if valid:
        assert function(value) is None
    else:
        with pytest.raises(error) as caught:
            function(invalid)
        assert caught.value.code == code
    request.node.canonical_ids = [canonical]


@pytest.mark.parametrize("provider", [False, True], ids=["VCP", "PROVIDER"])
def test_unknown_schema_root_is_rejected(provider, request):
    if provider:
        with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
            pc.load_provider_schema("not-a-published-root")
    else:
        with pytest.raises(ProtocolError, match="PROTOCOL_STRUCTURE"):
            vcp.load_schema("not-a-published-root")
    request.node.canonical_ids = [
        "CM.SDK.PROVIDER.SCHEMA.LOAD" if provider else "CM.SDK.SCHEMA.LOAD"
    ]


def test_exact_serializer_bytes_and_explicit_null_payload(request):
    from openverify.provider import Outcome
    from openverify.serialization import serialize, to_data

    value = Result(disposition="SKIPPED", output=None)
    assert to_data(value) == {
        "protocol": "draft",
        "disposition": "SKIPPED",
        "evidence": [],
        "usage": {},
        "output": None,
    }
    assert (
        serialize(value)
        == '{"disposition":"SKIPPED","evidence":[],"output":null,"protocol":"draft","usage":{}}'
    )
    outcome = Outcome(invocation_id="a", state="COMPLETED", output=None)
    assert pc.wire_data(outcome) == {"invocation_id": "a", "state": "COMPLETED", "output": None}
    assert pc.serialize(outcome) == '{"invocation_id":"a","state":"COMPLETED","output":null}'
    request.node.canonical_ids = [
        "CM.SDK.SERIALIZE.BYTES",
        "CM.SDK.SERIALIZE.DATA",
        "CM.SDK.PROVIDER.SERIALIZE",
        "CM.SDK.PROVIDER.WIRE_DATA",
    ]
