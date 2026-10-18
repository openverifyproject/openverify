"""Source-derived boundary witnesses; expected data never comes from the SUT."""

import asyncio
import json
import sys
from itertools import product

import pytest

from openverify import Graph, ProtocolError, Relay, parse_result, parse_run_record
from openverify.dataflow import resolve_inputs, validate_port
from openverify.model import ExecutionObservation, InputPort, Measurement, Node
from openverify.provider import ProviderContractError, parse_invocation
from openverify.provider.stdio import StdioSessionValidator
from openverify.relay import provider
from openverify.relay.adapters.catalog import Catalog
from openverify.serialization import to_data
from openverify.standard.common import judge, object_schema
from openverify.standard.text import check_text
from tests.unit.test_provider_contract import invocation_data, manifest_data

from .test_snapshot import ROOT, node


@pytest.mark.parametrize(
    "handler,default,present",
    list(product(["BLOCK", "OMIT"], [None, 29], [False, True])),
    ids=lambda x: str(x),
)
def test_unused_default_never_substitutes(handler, default, present, request):
    p = InputPort.model_validate(
        {
            "name": "x",
            "schema": True,
            "required": handler == "BLOCK",
            "on_unavailable": handler,
            "default": {"kind": "CONSTANT", "value": default},
        }
    )
    request.node.canonical_ids = ["CM.VCP.DATA.DEFAULT.CONSTANT"]
    validate_port(p)
    n = Node.model_validate(
        {**node("n"), "inputs": [to_data(p)], "bindings": {"x": {"kind": "RUN_INPUT", "name": "x"}}}
    )
    inputs, resolutions, blocked = resolve_inputs(n, {"x": 17} if present else {}, {}, None)
    request.node.expected = {
        "inputs": {"x": 17} if present else {},
        "status": "AVAILABLE" if present else "ABSENT",
        "used_default": False,
        "blocked": not present and handler == "BLOCK",
    }
    request.node.actual = {
        "inputs": inputs,
        "status": resolutions["x"].status,
        "used_default": resolutions["x"].used_default,
        "blocked": blocked,
    }
    assert request.node.actual == request.node.expected
    assert ("value" in resolutions["x"].model_fields_set) == present


@pytest.mark.parametrize("handler", ["BLOCK", "OMIT"])
def test_unused_default_still_validated(handler, request):
    request.node.canonical_ids = ["CM.VCP.DATA.DEFAULT.CONSTANT"]
    p = InputPort.model_validate(
        {
            "name": "x",
            "schema": {"type": "integer"},
            "required": handler == "BLOCK",
            "on_unavailable": handler,
            "default": {"kind": "CONSTANT", "value": None},
        }
    )
    with pytest.raises(ProtocolError, match="DATAFLOW_VALUE"):
        validate_port(p)


@pytest.mark.parametrize("version", ["1", "Draft", "", "0.1"])
def test_invocation_rejects_unsupported_vcp_marker(version, request):
    request.node.canonical_ids = ["CM.PROVIDER.COMPAT.VCP_FIELDS"]
    with pytest.raises(ProviderContractError) as caught:
        parse_invocation({**invocation_data(), "vcp_version": version})
    assert caught.value.code == "INVALID_INVOCATION"


@pytest.mark.parametrize(
    "finding",
    [None, False, 0, "", [], {}],
    ids=["NULL", "FALSE", "ZERO", "EMPTY_STRING", "EMPTY_ARRAY", "EMPTY_OBJECT"],
)
def test_no_findings_arbitrary_json_is_valid_evidence(finding, request):
    result = judge([finding])
    parsed = parse_result(to_data(result))
    assert parsed.verdict == "FAIL"
    assert parsed.output["findings"] == [finding]
    assert len(parsed.evidence) == 1
    assert parsed.evidence[0].structured_data == ({"finding": None} if finding is None else finding)


@pytest.mark.parametrize("count", [10000, 10001])
def test_pattern_findings_observation_bound(count, monkeypatch):
    import json
    from types import SimpleNamespace

    from openverify.standard import text

    async def capture(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps([False] * count))

    # A deterministic process-boundary replacement; no malformed external provider.
    monkeypatch.setattr(text, "capture", capture)
    if count == 10001:
        with pytest.raises(ValueError, match="10000 observation limit"):
            asyncio.run(check_text({"text": ""}, {"patterns": ["x"] * count}))
    else:
        r = asyncio.run(check_text({"text": ""}, {"patterns": ["x"] * count}))
        assert len(r.output["findings"]) == len(r.evidence) == 10000
        assert r.verdict == "FAIL"


def test_timing_preserves_every_provider_dimension():
    authored = {
        k: {"unit": u, "kind": "EXACT", "value": v}
        for k, u, v in [
            ("wall_time", "ms", 17),
            ("relay_wall_time", "ticks", 29),
            ("relay_wall_time_2", "work", 31),
        ]
    }

    @provider(
        provider_id="com.example.timing",
        capability_id="com.example.timing",
        kind="DERIVE",
        input_schema=object_schema({}),
        output_schema=object_schema({}),
        config_schema=object_schema({}),
    )
    async def implementation(inputs, config):
        return ExecutionObservation(
            outputs={}, usage={k: Measurement.model_validate(v) for k, v in authored.items()}
        )

    catalog = Catalog()
    catalog.register(implementation)
    graph = Graph("timing-collision")
    graph.derive("n", "com.example.timing", inputs={}, outputs={})
    record = Relay(catalog=catalog).run_sync(graph, inputs={}).record
    n = record.nodes[0]
    assert {k: to_data(n.usage[k]) for k in authored} == authored
    assert {k: to_data(v) for k, v in n.observation.usage.items()} == authored
    assert set(n.usage) == set(authored) | {"relay_wall_time_3"}
    assert n.usage["relay_wall_time_3"].unit == "s"
    assert n.usage["relay_wall_time_3"].kind == "EXACT"
    assert n.usage["relay_wall_time_3"].value >= 0
    assert parse_run_record(to_data(record)) == record


@pytest.mark.parametrize("code,valid", [(-32601, True), (-32000, False), (-32602, False)])
def test_unknown_rpc_response_and_session_continuity(code, valid):
    session = StdioSessionValidator()
    session.runner_message(
        {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]},
        }
    )
    session.provider_message(
        {
            "jsonrpc": "2.0",
            "id": "init",
            "result": {"contract_version": "0.1", "manifest": manifest_data()},
        }
    )
    session.runner_message({"jsonrpc": "2.0", "id": "unknown", "method": "unknown", "params": {}})
    response = {
        "jsonrpc": "2.0",
        "id": "unknown",
        "error": {"code": code, "message": "Method not found"},
    }
    if not valid:
        with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
            session.provider_message(response)
        return
    session.provider_message(response)
    session.runner_message(
        {"jsonrpc": "2.0", "id": "next", "method": "invoke", "params": invocation_data()}
    )
    session.provider_message(
        {
            "jsonrpc": "2.0",
            "id": "next",
            "result": {"invocation_id": "attempt-1", "state": "COMPLETED", "output": "hello"},
        }
    )
    session.finish()


def test_unknown_method_before_initialization_does_not_start_work():
    session = StdioSessionValidator()
    session.runner_message({"jsonrpc": "2.0", "id": "unknown", "method": "unknown", "params": {}})
    session.provider_message(
        {
            "jsonrpc": "2.0",
            "id": "unknown",
            "error": {"code": -32601, "message": "Method not found"},
        }
    )
    session.runner_message(
        {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]},
        }
    )
    session.provider_message(
        {
            "jsonrpc": "2.0",
            "id": "init",
            "result": {"contract_version": "0.1", "manifest": manifest_data()},
        }
    )
    session.finish()


def test_stdio_invalid_invoke_uses_invalid_params_error(request):
    from openverify.provider.stdio import encode_frame

    async def scenario():
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(ROOT / "tests/golden_v4/stdio_peer.py"),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT,
        )

        async def exchange(message):
            process.stdin.write(encode_frame(message))
            await process.stdin.drain()
            async with asyncio.timeout(10):
                header = await process.stdout.readuntil(b"\r\n\r\n")
                return json.loads(
                    await process.stdout.readexactly(int(header.split(b":", 1)[1].strip()))
                )

        try:
            initialized = await exchange(
                {
                    "jsonrpc": "2.0",
                    "id": "init",
                    "method": "initialize",
                    "params": {
                        "supported_contract_versions": ["0.1"],
                        "supported_vcp_versions": ["draft"],
                    },
                }
            )
            assert initialized["result"]["contract_version"] == "0.1"
            error = await exchange(
                {"jsonrpc": "2.0", "id": "invalid", "method": "invoke", "params": {}}
            )
            assert error["id"] == "invalid"
            assert error["error"]["code"] == -32602
            assert error["error"]["data"]["code"] == "INVALID_INVOCATION"
        finally:
            process.stdin.close()
            async with asyncio.timeout(10):
                await process.wait()

    asyncio.run(scenario())
    request.node.canonical_ids = ["CM.PROVIDER.RPC.RESERVED_ERRORS.INVALID_INVOKE_PARAMS"]
