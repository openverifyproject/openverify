"""Deterministically controlled public runtime experiments; no production internals."""

from __future__ import annotations

import asyncio
import json
import tempfile
import sys
from copy import deepcopy
from pathlib import Path

from tests.golden_v02.adapters.public import ScriptedTransport, manifest_for, prepare
from tools.golden_v02.build_baseline import node, port, scenario, behavior
from tools.golden_v02.compare import equal
from tools.golden_v02.execution import AdapterGap


def basic(ids=("a",), edges=()):
    nodes = [node(i) for i in ids]
    return scenario(nodes, list(edges), {i: behavior({"value": i}) for i in ids}, {})


class Controlled(ScriptedTransport):
    def __init__(self, value):
        self.started = asyncio.Event()
        self.release_event = asyncio.Event()
        self.done = asyncio.Event()
        super().__init__(
            {"outputs": {"value": value}}, [], entered=self.started, release=self.release_event
        )

    async def invoke(self, request, emit):
        try:
            return await super().invoke(request, emit)
        finally:
            self.done.set()


async def _finish(task, controls):
    for c in controls:
        c.release_event.set()
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def concurrency(variant):
    if variant in ("ready_overlap", "dependency_barrier", "completion_order"):

        async def run_order(order):
            a, b = Controlled("a"), Controlled("b")
            sc = basic(("a", "b"), [("a", "b")] if variant == "dependency_barrier" else [])
            bound = prepare(sc, transports={"a": a, "b": b})
            task = asyncio.create_task(bound.invoke())
            try:
                await asyncio.wait_for(a.started.wait(), 5)
                if variant == "dependency_barrier":
                    assert not b.started.is_set(), "successor entered before producer released"
                    a.release_event.set()
                    await asyncio.wait_for(b.started.wait(), 5)
                else:
                    await asyncio.wait_for(b.started.wait(), 5)
                controls = {"a": a, "b": b}
                for identity in order:
                    controls[identity].release_event.set()
                    await asyncio.wait_for(controls[identity].done.wait(), 5)
                record = await asyncio.wait_for(task, 5)
                assert all(n["state"] == "SUCCESS" for n in record["nodes"])
                return {n["node_id"]: n["information"] for n in record["nodes"]}
            finally:
                await _finish(task, [a, b])

        first = await run_order(("a", "b"))
        if variant == "completion_order":
            equal(first, await run_order(("b", "a")))
        return {"verified": True, "observed_information": first}
    if variant == "control_barrier":
        active = set()
        history = []

        class Activity(ScriptedTransport):
            async def invoke(self, request, emit):
                identity = request.invocation.invocation_id
                if request.invocation.capability_id.endswith("control"):
                    assert not active, "Control overlaps active work"
                active.add(identity)
                history.append(("enter", identity))
                try:
                    await asyncio.sleep(0)  # scheduler yield; no elapsed-time assertion
                    return await super().invoke(request, emit)
                finally:
                    active.remove(identity)
                    history.append(("leave", identity))

        sc = basic(("a", "b"))
        c = node("control", "CONTROL")
        sc["definition"]["graph"]["nodes"].insert(1, c)
        sc["behaviors"]["control"] = {
            "outputs": {"decision": {"protocol": "draft", "kind": "STOP_SUCCESS"}}
        }
        transports = {
            n["id"]: Activity(sc["behaviors"][n["id"]], [])
            for n in sc["definition"]["graph"]["nodes"]
        }
        record = await prepare(sc, transports=transports).invoke()
        assert any(n.get("reason") == "CONTROL_STOP" for n in record["nodes"])
        return {"verified": True, "history": history}
    if variant == "shared_provider_serial":
        from openverify import Relay
        from openverify.relay import provider
        from openverify.relay.adapters.catalog import Catalog

        active = maximum = 0
        entered = asyncio.Event()
        release = asyncio.Event()

        @provider(
            provider_id="com.example.serial",
            capability_id="com.example.golden.derive",
            kind="DERIVE",
            input_schema=True,
            output_schema=True,
            config_schema=True,
        )
        async def shared(inputs, config):
            nonlocal active, maximum
            active += 1
            maximum = max(active, maximum)
            entered.set()
            try:
                await release.wait()
                return {"value": "shared"}
            finally:
                active -= 1

        catalog = Catalog()
        catalog.register(shared)
        task = asyncio.create_task(
            Relay(catalog=catalog).run(json.dumps(basic(("a", "b"))["definition"]), inputs={})
        )
        try:
            await asyncio.wait_for(entered.wait(), 5)
            release.set()
            await asyncio.wait_for(task, 5)
            equal(1, maximum)
        finally:
            release.set()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        return {"verified": True, "max_active": maximum}
    raise AdapterGap("concurrency variant " + variant)


async def cancellation(variant):
    from openverify.lifecycle import Cancellation

    token = Cancellation()
    control = Controlled("a")
    bound = prepare(basic(), transports={"a": control})
    if variant == "before_dispatch":
        token.cancel("golden.before")
        record = await bound.invoke(cancellation=token)
        assert not control.started.is_set()
        equal("CANCELLED", record["nodes"][0]["result"]["disposition"])
        equal("BEFORE_START", record["cancellation"]["phase"])
        return {"verified": True, "record": record}
    if variant == "after_terminal":
        control.release_event.set()
        record = await bound.invoke(cancellation=token)
        snapshot = deepcopy(record)
        token.cancel("too.late")
        equal(snapshot, record)
        equal("SUCCESS", record["nodes"][0]["state"])
        return {"verified": True}
    task = asyncio.create_task(
        bound.invoke(cancellation=token if variant != "task_cancel" else None)
    )
    try:
        await asyncio.wait_for(control.started.wait(), 5)
        if variant == "task_cancel":
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                return {"verified": True, "cancelled_error": True}
            raise AssertionError("task cancellation fabricated a completed result")
        token.cancel("golden.during")
        control.release_event.set()
        record = await asyncio.wait_for(task, 5)
        n = record["nodes"][0]
        equal("CANCELLED", n["state"])
        equal({}, n["information"])
        equal("RUNNING", record["cancellation"]["phase"])
        return {"verified": True, "record": record}
    finally:
        await _finish(task, [control])


async def isolation(variant):
    if variant == "cancel_one_run":
        results = await asyncio.gather(cancellation("during_invocation"), _echo_runs())
        return {"verified": True, "runs": len(results)}
    if variant == "separate_worktrees":
        from tests.golden_v02.adapters.standard import worktree_isolation

        return await worktree_isolation()
    if variant in ("distinct_inputs", "distinct_bindings"):
        return await _echo_runs(distinct=variant == "distinct_bindings")
    raise AdapterGap("isolation variant " + variant)


async def _echo_runs(distinct=False):
    from openverify.provider import Outcome

    class Echo(ScriptedTransport):
        async def invoke(self, request, emit):
            await asyncio.sleep(0)
            self.calls.append(deepcopy(request.invocation.input))
            return Outcome(
                invocation_id=request.invocation.invocation_id,
                state="COMPLETED",
                output={"value": deepcopy(request.invocation.input["data"])},
            )

    n = node("a", inputs=[port("data")], bindings={"data": {"kind": "RUN_INPUT", "name": "data"}})
    sc = scenario([n], [], {"a": behavior({})}, {}, declarations=[port("data")])
    echo = Echo({}, [])
    bound = prepare(sc, transports={"a": echo})
    if distinct:
        other = deepcopy(sc)
        other["definition"]["graph"]["nodes"][0]["id"] = "b"
        other["behaviors"] = {"b": behavior({})}
        bound2 = prepare(other, transports={"b": Echo({}, [])})
    else:
        bound2 = bound

    async def invoke(b, value):
        run = await b.relay.run(json.dumps(b.definition), inputs={"data": value})
        return json.loads(run.to_json())

    a, b = await asyncio.gather(
        invoke(bound, {"run": "first", "value": True}),
        invoke(bound2, {"run": "second", "value": 1}),
    )
    assert a["run_id"] != b["run_id"]
    equal({"run": "first", "value": True}, a["nodes"][0]["information"]["value"])
    equal({"run": "second", "value": 1}, b["nodes"][0]["information"]["value"])
    if distinct:
        assert (
            a["nodes"][0]["provider_binding"]["provider_id"]
            != b["nodes"][0]["provider_binding"]["provider_id"]
        )
    return {"verified": True, "run_ids": [a["run_id"], b["run_id"]]}


async def timeout(variant):
    if variant == "delayed_provider":
        c = Controlled("a")
        bound = prepare(basic(), transports={"a": c}, timeout=0.05)
        try:
            record = await asyncio.wait_for(bound.invoke(), 5)
            equal("ERROR", record["nodes"][0]["state"])
            equal({}, record["nodes"][0]["information"])
            assert c.started.is_set()
            return {"verified": True, "record": record}
        finally:
            c.release_event.set()
    if variant == "ignores_cancel_stdio":
        return await external("ignores_cancel")
    raise AdapterGap("timeout variant " + variant)


async def external(mode, *, manifest_change=False):
    from openverify.relay.adapters.stdio import StdioTransport
    from openverify.provider import wire_data
    from tools.golden_v02.verify_manifest import ROOT

    sc = basic()
    requirement = sc["definition"]["graph"]["nodes"][0]["operation"]
    manifest = manifest_for("a", requirement)
    with tempfile.TemporaryDirectory(prefix="golden-stdio-") as folder:
        path = Path(folder) / "peer.json"
        advertised = wire_data(manifest)
        if manifest_change:
            advertised["provider_version"] = "other"
        path.write_text(
            json.dumps(
                {
                    "manifest": advertised,
                    "behaviors": {
                        requirement["capability_id"]: {"mode": mode, "outputs": {"value": "a"}}
                    },
                }
            ),
            encoding="utf-8",
        )
        transport = StdioTransport(
            (sys.executable, str(ROOT / "tools/golden_v02/stdio_provider.py"), "--spec", str(path)),
            str(ROOT),
        )
        bound = prepare(
            sc, transports={"a": transport}, timeout=0.3 if mode == "ignores_cancel" else 3
        )
        record = await asyncio.wait_for(bound.invoke(), 8)
        expect_success = mode in ("valid", "stderr") and not manifest_change
        equal("SUCCESS" if expect_success else "ERROR", record["nodes"][0]["state"])
        if not expect_success:
            equal({}, record["nodes"][0]["information"])
        return {"verified": True, "record": record}


async def binding(variant):
    if variant == "identity_substitution":
        return await external("valid", manifest_change=True)
    from openverify import Relay
    from openverify.model import ProviderBinding
    from openverify.relay import RuntimeConfig
    from openverify.relay.adapters.catalog import Catalog

    sc = basic()
    req = sc["definition"]["graph"]["nodes"][0]["operation"]
    catalog = Catalog()
    calls = []
    manifest = manifest_for("a", req)
    if variant != "no_match":
        catalog.register_transport(manifest, ScriptedTransport({"outputs": {"value": "a"}}, calls))
    if variant in ("ambiguous", "explicit_correct", "explicit_incompatible"):
        catalog.register_transport(
            manifest_for("b", req), ScriptedTransport({"outputs": {"value": "b"}}, calls)
        )
    settings = {}
    if variant.startswith("explicit") or variant in ("provider_version", "capability_version"):
        binding = {"provider_id": manifest.provider_id, "provider_version": "1", **req}
        if variant == "explicit_incompatible":
            binding["capability_id"] = "com.example.absent"
        if variant == "provider_version":
            binding["provider_version"] = "2"
        if variant == "capability_version":
            binding["capability_version"] = "2"
        settings["a"] = ProviderBinding(**binding)
    relay = Relay(catalog=catalog, config=RuntimeConfig(bindings=settings))
    should_reject = variant not in ("unique", "explicit_correct")
    try:
        run = await relay.run(json.dumps(sc["definition"]), inputs={})
    except Exception as exc:
        assert should_reject, exc
        from openverify.errors import ProtocolError
        from openverify.provider import ProviderContractError

        assert isinstance(exc, (ProtocolError, ProviderContractError)), (
            "unstructured binding rejection"
        )
        assert not calls, "incompatible provider invoked before rejection"
        return {"verified": True, "rejection": getattr(exc, "code", type(exc).__name__)}
    assert not should_reject, "invalid/ambiguous binding accepted"
    equal(1, len(calls))
    equal(manifest.provider_id, run.record.nodes[0].provider_binding.provider_id)
    return {"verified": True}


async def security(variant):
    from tests.golden_v02.adapters.standard import security_experiment

    return await security_experiment(variant)


async def experiment(payload):
    function = {
        "concurrency": concurrency,
        "isolation": isolation,
        "cancellation": cancellation,
        "timeout": timeout,
        "binding": binding,
        "security": security,
    }.get(payload["experiment"])
    if function is None:
        raise AdapterGap("runtime experiment " + payload["experiment"])
    return await function(payload["variant"])
