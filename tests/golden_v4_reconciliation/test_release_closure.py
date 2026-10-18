"""Finite v0.1 closure witnesses derived from contracts, not runtime recording."""

import asyncio
import base64
import hashlib
import json
import sys

import pytest

from openverify import Graph, ProtocolError, Relay
from openverify.lifecycle import Cancellation
from openverify.model import Evidence, ExecutionError, ExecutionObservation, Measurement
from openverify.provider import Invocation, wire_data
from openverify.relay.adapters.memory import MemoryStore
from openverify.relay.entrypoints.service import GraphService
from openverify.serialization import to_data
from openverify.standard.control import gate_decision
from openverify.standard.filesystem import FileAccess

from .test_public_boundaries import decorate
from .test_snapshot import ROOT


def capture(request, ids, expected, actual):
    request.node.canonical_ids = ids
    request.node.expected = expected
    request.node.actual = actual
    assert actual == expected


@pytest.mark.parametrize(
    "body,expected",
    [(b"{", -32700), (b'{"jsonrpc":"1.0","id":"bad","method":"unknown","params":{}}', -32600)],
    ids=["PARSE_ERROR", "INVALID_REQUEST"],
)
def test_stdio_reserved_errors_at_real_server(body, expected, request):
    async def run():
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(ROOT / "tests/golden_v4/stdio_peer.py"),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT,
        )
        try:
            process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
            await process.stdin.drain()
            async with asyncio.timeout(10):
                header = await process.stdout.readuntil(b"\r\n\r\n")
                response = json.loads(
                    await process.stdout.readexactly(int(header.split(b":", 1)[1].strip()))
                )
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == (None if expected == -32700 else "bad")
            return response["error"]["code"]
        finally:
            process.stdin.close()
            async with asyncio.timeout(10):
                await process.wait()

    capture(
        request,
        ["CM.PROVIDER.RPC.RESERVED_ERRORS.NUMERIC_CODES", "CM.SDK.SERVE_STDIO"],
        expected,
        asyncio.run(run()),
    )


@pytest.mark.parametrize(
    "status",
    [
        "PASS",
        "FAIL",
        "UNKNOWN",
        "ERROR",
        "SKIPPED",
        "DEFERRED",
        "CANCELLED",
        "NOT_APPLICABLE",
        "SCORE_ONLY",
    ],
    ids=lambda x: x,
)
def test_gate_exhausts_semantic_result_classes(status, request):
    raw = {
        "protocol": "draft",
        "disposition": "EXECUTED",
        "execution_outcome": "SUCCESS",
        "applicability": "APPLICABLE",
        "determination": "KNOWN",
    }
    if status in ("PASS", "FAIL"):
        raw["verdict"] = status
    elif status == "SCORE_ONLY":
        raw["score"] = 1
    elif status == "UNKNOWN":
        raw["determination"] = "UNKNOWN"
    elif status == "NOT_APPLICABLE":
        raw.pop("determination")
        raw["applicability"] = "NOT_APPLICABLE"
    elif status == "ERROR":
        raw = {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": "ERROR"}
    else:
        raw = {"protocol": "draft", "disposition": status}
    expected = {
        "decision": {
            "protocol": "draft",
            "kind": "CONTINUE" if status == "PASS" else "STOP_FAILURE",
        }
    }
    capture(
        request,
        ["CM.RELAY.STANDARD.GATE"],
        expected,
        asyncio.run(gate_decision({"checked": raw}, {})),
    )


def test_invalid_gate_input_is_rejection_not_denial(request):
    with pytest.raises(ProtocolError) as caught:
        asyncio.run(
            gate_decision({"checked": {"protocol": "draft", "disposition": "EXECUTED"}}, {})
        )
    capture(request, ["CM.RELAY.STANDARD.GATE.INVALID"], "RESULT_STATE", str(caught.value.code))


def test_storage_duplicate_and_both_snapshot_directions(request):
    store = MemoryStore()
    run = Relay(store=store).run_sync(Graph("snapshot"), inputs={}).record
    original = to_data(run)
    with pytest.raises(ValueError, match="already stored"):
        store.put(run)
    run.initial_context["mutation"] = 17
    returned = store.get(run.run_id)
    assert to_data(returned) == original
    returned.initial_context["mutation"] = 29
    capture(
        request,
        ["CM.RELAY.STORE.DUPLICATE", "CM.RELAY.STORE.COPY", "CM.RELAY.PORT.RecordStore.get"],
        original,
        to_data(store.get(run.run_id)),
    )


@pytest.mark.parametrize(
    "value,valid",
    [("first", True), ("", False), (None, False), (17, False)],
    ids=["FIRST_REASON", "EMPTY", "NULL", "NUMBER"],
)
def test_cancellation_token_first_reason_and_rejections(value, valid, request):
    token = Cancellation()
    assert token.reason is None
    if valid:
        token.cancel(value)
        token.cancel("second")
        assert token.reason == "first"
    else:
        with pytest.raises(ValueError):
            token.cancel(value)
        assert token.reason is None
    request.node.canonical_ids = ["CM.SDK.CANCELLATION.TOKEN"]
    request.node.expected = {"reason": "first" if valid else None}
    request.node.actual = {"reason": token.reason}


def test_fileaccess_snapshot_boundaries_and_root_selection(tmp_path, request):
    access = FileAccess((tmp_path,), max_bytes=3)
    path = tmp_path / "input.bin"
    path.write_bytes(b"\x00ab")
    content, identity = access.read(path)
    assert content == b"\x00ab"
    assert identity == {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(b"\x00ab").hexdigest(),
        "size": 3,
    }
    assert base64.b64encode(content).decode() == "AGFi"
    path.write_bytes(b"\x00abc")
    with pytest.raises(ValueError, match="3 byte limit"):
        access.read(path)
    with pytest.raises(PermissionError):
        access.path(str(tmp_path.parent / "outside"))
    with pytest.raises(ValueError, match="exactly one"):
        FileAccess((tmp_path, tmp_path.parent)).path("input.bin")
    request.node.canonical_ids = [
        "CM.SDK.FILEACCESS.ROOTS",
        "CM.SDK.FILEACCESS.RELATIVE",
        "CM.SDK.FILEACCESS.BOUNDS",
        "CM.SDK.FILEACCESS.SNAPSHOT",
        "CM.RELAY.STANDARD.FILES.IDENTITY",
    ]
    request.node.expected = {"bytes_hex": "006162", "size": 3}
    request.node.actual = {"bytes_hex": content.hex(), "size": identity["size"]}


@pytest.mark.parametrize("mode", ["EVIDENCE_USAGE_ERROR", "BUDGET", "CANCEL"], ids=lambda x: x)
def test_function_provider_observation_failure_channels(mode, request):
    calls = []

    @decorate("DERIVE")
    async def compute(inputs, config):
        calls.append(inputs)
        if mode == "CANCEL":
            raise asyncio.CancelledError()
        return ExecutionObservation(
            outputs={},
            evidence=[Evidence(message="authored")],
            usage={"token": Measurement(unit="token", kind="EXACT", value=17)},
            error=ExecutionError(code="com.example.failure", message="authored"),
        )

    raw = {
        "invocation_id": "attempt",
        "contract_version": "0.1",
        "capability_id": "com.example.compute",
        "capability_version": "1",
        "vcp_version": "draft",
        "input": {},
        "config": {},
    }
    if mode == "BUDGET":
        raw["resource_budget"] = {"token": {"unit": "token", "kind": "EXACT", "value": 29}}

    async def run():
        return [wire_data(item) async for item in compute.invoke(Invocation.model_validate(raw))]

    if mode == "BUDGET":
        with pytest.raises(ValueError, match="cannot enforce") as caught:
            asyncio.run(run())
        assert calls == []
        request.node.canonical_ids = [
            "CM.SDK.FUNCTION_PROVIDER.BUDGET",
            "CM.PROVIDER.BUDGET.ENFORCE.PREACCEPT",
        ]
        request.node.expected = {"calls": [], "raised": "ValueError"}
        request.node.actual = {"calls": calls, "raised": type(caught.value).__name__}
    elif mode == "CANCEL":
        with pytest.raises(asyncio.CancelledError) as cancelled:
            asyncio.run(run())
        assert calls == [{}]
        request.node.canonical_ids = ["CM.SDK.FUNCTION_PROVIDER.TASK_CANCEL"]
        request.node.expected = {"calls": [{}], "raised": "CancelledError"}
        request.node.actual = {"calls": calls, "raised": type(cancelled.value).__name__}
    else:
        observed = asyncio.run(run())
        assert [v.get("kind", v.get("state")) for v in observed] == [
            "evidence",
            "resource_usage",
            "ERROR",
        ]
        assert [v["sequence"] for v in observed[:-1]] == [1, 2]
        assert observed[0]["payload"] == {"message": "authored"}
        assert (
            observed[1]["payload"]
            == observed[-1]["resource_usage"]
            == {"token": {"unit": "token", "kind": "EXACT", "value": 17}}
        )
        assert observed[-1]["error"] == {
            "code": "openverify.computation_error",
            "message": "com.example.failure: authored",
        }
        request.node.canonical_ids = ["CM.SDK.FUNCTION_PROVIDER.OBSERVATION"]
        request.node.expected = {
            "kinds": ["evidence", "resource_usage", "ERROR"],
            "sequences": [1, 2],
            "usage": {"token": {"unit": "token", "kind": "EXACT", "value": 17}},
        }
        request.node.actual = {
            "kinds": [v.get("kind", v.get("state")) for v in observed],
            "sequences": [v["sequence"] for v in observed[:-1]],
            "usage": observed[-1]["resource_usage"],
        }


def test_service_concurrency_limit_uses_barriers(request):
    async def scenario():
        entered, release, second_requested = asyncio.Event(), asyncio.Event(), asyncio.Event()
        active = 0
        maximum = 0
        relay = Relay()
        original = relay.run

        async def measured(*args, **kwargs):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            entered.set()
            try:
                await release.wait()
                return await original(*args, **kwargs)
            finally:
                active -= 1

        relay.run = measured
        service = GraphService(relay, {"a": Graph("limited")}, max_concurrent_runs=1)
        first = asyncio.create_task(service.run_graph("a", {}))
        await entered.wait()

        async def second():
            second_requested.set()
            return await service.run_graph("a", {})

        next_run = asyncio.create_task(second())
        await second_requested.wait()
        # second() executes until its next suspension (the locked semaphore), so
        # the event gives a deterministic scheduling barrier without any sleep.
        assert active == maximum == 1
        release.set()
        a, b = await asyncio.gather(first, next_run)
        assert a["run_id"] != b["run_id"]
        assert maximum == 1
        return {
            "maximum": maximum,
            "distinct_run_ids": a["run_id"] != b["run_id"],
            "active_after": active,
        }

    request.node.actual = asyncio.run(scenario())
    request.node.expected = {"maximum": 1, "distinct_run_ids": True, "active_after": 0}
    assert request.node.actual == request.node.expected
    request.node.canonical_ids = [
        "CM.RELAY.SERVICE.CONCURRENCY",
        "CM.SDK.SERVICE.GRAPHSERVICE.RUN_GRAPH.LIMIT",
    ]
