"""Registry/wire compatibility and demonstrated public boundary regressions."""

import ast
import asyncio
import json
import re
from pathlib import Path

import pytest

from openverify import Relay
from openverify.error_codes import VcpErrorCode
from openverify.errors import ProtocolError
from openverify.provider import ProviderContractError, ProviderError, parse_outcome, serialize
from openverify.provider_codes import ProviderErrorCode
from openverify.relay.error_codes import RelayErrorCode
from openverify.relay.errors import RelayError
from openverify.relay.templates import text_graph

ROOT = Path(__file__).resolve().parents[1]


def test_error_code_literals_match_owned_registries():
    known = {
        c.value
        for vocabulary in (VcpErrorCode, ProviderErrorCode, RelayErrorCode)
        for c in vocabulary
    }
    for path in (ROOT / "src/openverify").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func.id if isinstance(node.func, ast.Name) else ""
            values = [kw.value for kw in node.keywords if kw.arg == "code"]
            if (
                callee in ("ProtocolError", "ProviderContractError", "RelayError", "fail")
                and node.args
            ):
                values.append(node.args[0])
            for value in values:
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and re.fullmatch(r"[A-Z][A-Z_]+", value.value)
                ):
                    assert value.value in known, (path, value.lineno, value.value)


def test_reserved_provider_registry_matches_normative_table():
    text = (ROOT / "provider-contract/spec/draft/errors.md").read_text(encoding="utf-8")
    assert set(re.findall(r"\| ([A-Z_]+) \|", text)) == {c.value for c in ProviderErrorCode}
    assert not (set(VcpErrorCode) & set(ProviderErrorCode))
    assert not (set(RelayErrorCode) & set(ProviderErrorCode))
    assert not (set(RelayErrorCode) & set(VcpErrorCode))


def test_vcp_registry_consistency_and_existing_sdk_diagnostics():
    text = (ROOT / "spec/draft/conformance.md").read_text(encoding="utf-8")
    text = text.split("Errors have code", 1)[1].split("Paths use", 1)[0]
    binding = (ROOT / "spec/draft/provider-binding.md").read_text(encoding="utf-8")
    text += binding.split("Execution errors expose stable codes:", 1)[1].split(
        "## OPEN QUESTIONS", 1
    )[0]
    declared = set(re.findall(r"\b[A-Z][A-Z_]+\b", text))
    policy = (ROOT / "spec/draft/execution-policy.md").read_text(encoding="utf-8")
    declared.update(re.findall(r"(?:raises|raise) ([A-Z_]+)", policy))
    declared.add("PROVIDER_BINDING_REQUIRED")
    declared -= {c.value for c in ProviderErrorCode} | {
        "JSON",
        "SDK",
        "VCP",
        "FAIL",
        "INPUT_UNAVAILABLE",
    }
    assert {c.value for c in VcpErrorCode} - declared == {"POLICY_ERROR", "RESULT_PROJECTION"}
    assert declared <= {c.value for c in VcpErrorCode}


def test_conforming_custom_sequence_catalog_remains_supported():
    from collections import UserList

    from openverify.standard import standard_catalog

    values = UserList(standard_catalog().providers())

    class Custom:
        def providers(self):
            return values

    run = asyncio.run(
        Relay(catalog=Custom()).run(text_graph(), inputs={"text": "Migration Rollback"})
    )
    assert run.results["all"].verdict == "PASS"


@pytest.mark.parametrize("code", list(VcpErrorCode))
def test_vcp_error_preserves_code_and_diagnostics(code: VcpErrorCode):
    error = ProtocolError(code.value, "diagnostic", "/graph", {"value": [False, 0, None]})
    assert error.code is code
    assert json.loads(json.dumps(error.as_dict())) == {
        "code": code.value,
        "message": "diagnostic",
        "path": "/graph",
        "details": {"value": [False, 0, None]},
    }


@pytest.mark.parametrize("code", list(ProviderErrorCode))
def test_provider_code_wire_roundtrip(code: ProviderErrorCode):
    error = ProviderContractError(code.value, "diagnostic", {"value": [False, 0, None]})
    assert error.code is code
    model = ProviderError(code=code.value, message="diagnostic", details=error.details)
    assert model.code is code
    raw = {"invocation_id": "attempt", "state": "ERROR", "error": error.as_dict()}
    parsed = parse_outcome(raw)
    assert parsed.error is not None and parsed.error.code is code
    assert json.loads(serialize(parsed)) == raw


@pytest.mark.parametrize("code", list(RelayErrorCode))
def test_relay_error_is_typed_without_wire_renaming(code: RelayErrorCode):
    error = RelayError(code.value, "diagnostic", details={"safe": True})
    assert error.code is code
    assert json.loads(json.dumps(error.as_dict()))["code"] == code.value


def test_provider_namespaced_errors_stay_extensible():
    error = ProviderError(code="com.example.tool_failed", message="diagnostic")
    assert error.code == "com.example.tool_failed"
    assert isinstance(error.code, str)


@pytest.mark.parametrize("port", ["catalog", "binder"])
def test_infrastructure_exception_has_typed_code_and_original_cause(port: str):
    failure = RuntimeError("host diagnostic")

    class Broken:
        def providers(self):
            raise failure

        def bind(self, *args):
            raise failure

    relay = Relay(**{port: Broken()})
    with pytest.raises(RelayError) as caught:
        asyncio.run(relay.run(text_graph(), inputs={"text": "Migration Rollback"}))
    error = caught.value
    assert error.code is (
        RelayErrorCode.CATALOG_FAILURE if port == "catalog" else RelayErrorCode.BINDER_FAILURE
    )
    assert error.__cause__ is failure
    assert error.details == {"cause_type": "RuntimeError", "cause_message": "host diagnostic"}


def test_nonconforming_catalog_rejection_is_structured():
    class Broken:
        def providers(self):
            return (object(),)

    with pytest.raises(RelayError) as caught:
        asyncio.run(
            Relay(catalog=Broken()).run(text_graph(), inputs={"text": "Migration Rollback"})
        )
    assert caught.value.code is RelayErrorCode.CATALOG_INVALID


def test_existing_structured_catalog_error_is_preserved():
    failure = ProviderContractError(
        "INVALID_PROVIDER_OUTPUT", "manifest diagnostic", {"field": "capabilities"}
    )

    class Broken:
        def providers(self):
            raise failure

    with pytest.raises(ProviderContractError) as caught:
        asyncio.run(
            Relay(catalog=Broken()).run(text_graph(), inputs={"text": "Migration Rollback"})
        )
    assert caught.value is failure
