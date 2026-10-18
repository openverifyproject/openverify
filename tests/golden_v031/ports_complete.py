"""Applicable contracts for all six injected ports, through actual tiny Relay runs.

get is explicitly exercised as a host retrieval surface after Relay.run; no
nonexistent Relay.get validation guarantee is asserted. Void returns are not a
judgment channel. Cancellation uses events, never timing sleeps.
"""
import asyncio
from collections import UserList
from copy import deepcopy
import json
from time import perf_counter_ns

from tools.golden_v02.compare import equal


def assert_record(record, value, *, failed=False):
    n = record["nodes"][0]
    equal(["n"], [x["node_id"] for x in record["nodes"]])
    equal({"payload": value}, record["run_inputs"])
    equal({"value": value}, n["input_values"])
    equal("AVAILABLE", n["input_resolutions"]["value"]["status"])
    equal({"kind": "RUN_INPUT", "name": "payload"}, n["input_resolutions"]["value"]["source"])
    equal(value, n["input_resolutions"]["value"]["value"])
    equal("com.example.golden.port", n["provider_binding"]["provider_id"])
    equal("1", n["provider_binding"]["provider_version"])
    equal(n["provider_binding"], record["provider_bindings"]["n"])
    equal("ERROR" if failed else "SUCCESS", n["state"])
    equal({} if failed else {"value": value}, n["information"])
    if failed:
        equal("ERROR", n["result"]["execution_outcome"])
        assert n["result"].get("verdict") is None
    else:
        equal({"value": value}, n["observation"]["outputs"])
        assert "n" not in record["final_results"]
    assert n["usage"]["wall_time"]["value"] >= 0


def mutation(record, value, failed=False):
    changed = deepcopy(record)
    changed["nodes"][0]["provider_binding"]["provider_version"] = "forged"
    changed["nodes"][0]["executor_version"] = "forged"
    changed["provider_bindings"]["n"]["provider_version"] = "forged"
    try:
        assert_record(changed, value, failed=failed)
    except AssertionError:
        return
    raise AssertionError("Coherent provider-version mutant escaped trusted manifest anchor")


async def execute(case, report):
    from openverify import Relay, parse_definition, parse_run_record
    from openverify.errors import ProtocolError
    from openverify.model import ExecutionError, ProviderBinding
    from openverify.provider import Outcome, ProviderEvent, ProviderContractError
    from openverify.relay.adapters.local import LocalDriver
    from openverify.relay.ports import AvailableProvider, InvocationReport
    from tests.golden_v02.adapters.public import manifest_for
    from tools.golden_v02.build_baseline import definition, node, port

    target, variant, expected = case["port"], case["variant"], case["expected"]
    failure = RuntimeError("scripted port failure")
    structured = ProviderContractError("INVALID_INPUT", "scripted rejection", {"field": "value"})
    n = node("n", inputs=[port("value", {"type": "integer"})],
             bindings={"value": {"kind": "RUN_INPUT", "name": "payload"}})
    d = parse_definition(definition([n], inputs=[port("payload", {"type": "integer"})]))
    manifest = manifest_for("unused", n["operation"], input_schema={"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"], "additionalProperties": False},
        output_schema={"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"], "additionalProperties": False})
    manifest = manifest.model_copy(update={"provider_id": "com.example.golden.port"})
    traces, saved, observed, calls = [], {}, [], []
    entered = {11: asyncio.Event(), 22: asyncio.Event()}
    release = {11: asyncio.Event(), 22: asyncio.Event()}
    cleaned = []
    is_controlled = variant in ("cancellation", "concurrency_isolation")

    def selected(port_name, name):
        return target == port_name and variant == name

    class Transport:
        async def invoke(self, request, emit):
            inv = request.invocation
            value = inv.input["value"]
            traces.append(("invoke", value))
            calls.append({"value": value, "input": deepcopy(inv.input), "invocation_id": inv.invocation_id})
            if is_controlled:
                entered[value].set()
                try:
                    await release[value].wait()
                finally:
                    cleaned.append(value)
            if selected("Transport", "exception"):
                raise failure
            if selected("Transport", "invalid_return"):
                return None
            if selected("Transport", "stream_failure"):
                emit(ProviderEvent(invocation_id=inv.invocation_id, sequence=1, kind="progress", payload={"phase": "entered"}))
                raise failure
            if selected("Observer", "mutate_event"):
                emit(ProviderEvent(invocation_id=inv.invocation_id, sequence=1, kind="progress", payload={"phase": "known", "value": value}))
            if selected("Transport", "wrong_sequence"):
                emit(ProviderEvent(invocation_id=inv.invocation_id, sequence=2, kind="progress", payload={}))
            if selected("Transport", "wrong_event_correlation"):
                emit(ProviderEvent(invocation_id="foreign", sequence=1, kind="progress", payload={}))
            if selected("Transport", "duplicate_event"):
                e = ProviderEvent(invocation_id=inv.invocation_id, sequence=1, kind="progress", payload={})
                emit(e)
                emit(e)
            output = {"value": "bad"} if selected("Transport", "bad_output") else {"value": value}
            return Outcome(invocation_id="foreign" if selected("Transport", "wrong_correlation") else inv.invocation_id,
                           state="COMPLETED", output=output)

    transport = Transport()
    available = AvailableProvider(manifest, transport)

    class FailingSequence(UserList):
        def __iter__(self):
            yield available
            raise failure

    class Catalog:
        def providers(self):
            traces.append(("providers", None))
            if selected("Catalog", "exception"):
                raise failure
            if selected("Catalog", "structured_error"):
                raise structured
            if selected("Catalog", "invalid_return"):
                return None
            if selected("Catalog", "generator"):
                return iter([available])
            if selected("Catalog", "iteration_failure"):
                return FailingSequence([available])
            if selected("Catalog", "duplicate_identity"):
                return (available, available)
            if selected("Catalog", "bad_manifest"):
                return (AvailableProvider(manifest.model_copy(update={"provider_id": "INVALID"}), transport),)
            return (available,)

    class Binder:
        def bind(self, requirement, providers, explicit=None):
            traces.append(("bind", None))
            equal(n["operation"]["capability_id"], requirement.capability_id)
            if selected("Binder", "exception"):
                raise failure
            if selected("Binder", "structured_error"):
                raise structured
            if selected("Binder", "invalid_return"):
                return None
            chosen = providers[0]
            if selected("Binder", "bad_manifest"):
                return AvailableProvider(chosen.manifest.model_copy(update={"provider_id": "INVALID"}), chosen.transport)
            if selected("Binder", "wrong_capability") or selected("Binder", "wrong_version"):
                cap = chosen.manifest.capabilities[0]
                changes = {"capability_id": "com.example.other"} if variant == "wrong_capability" else {"capability_version": "other"}
                return AvailableProvider(chosen.manifest.model_copy(update={"capabilities": [cap.model_copy(update=changes)]}), chosen.transport)
            if selected("Binder", "untrusted_transport"):
                return AvailableProvider(chosen.manifest, Transport())
            if selected("Binder", "rewrite_manifest"):
                chosen.manifest.capabilities[0].input_schema.clear()
            return chosen

    class BadEvents:
        def __iter__(self):
            raise failure
            yield

    class Driver:
        async def execute(self, provider, request, timeout, emit):
            traces.append(("execute", request.invocation.input["value"]))
            inv = request.invocation
            if selected("Driver", "exception"):
                raise failure
            if selected("Driver", "invalid_return"):
                return {"fabricated": True}
            if selected("Driver", "malformed_events"):
                return InvocationReport(events=(object(),))
            if selected("Driver", "iteration_failure"):
                return InvocationReport(events=BadEvents())
            if selected("Driver", "missing_terminal"):
                return InvocationReport()
            if selected("Driver", "wrong_correlation"):
                return InvocationReport(Outcome(invocation_id="foreign", state="COMPLETED", output={"value": 11}))
            if selected("Driver", "forged_output_error"):
                return InvocationReport(Outcome(invocation_id=inv.invocation_id, state="COMPLETED", output={"value": 11}),
                                        output_error=ExecutionError(code="INVALID_PROVIDER_OUTPUT", message="fabricated"))
            if selected("Driver", "bad_output"):
                return InvocationReport(Outcome(invocation_id=inv.invocation_id, state="COMPLETED", output={"value": "wrong"}))
            if selected("Driver", "event_after_terminal"):
                from openverify.relay.adapters.inprocess import InProcessTransport

                class Peer:
                    async def invoke(self, invocation):
                        yield Outcome(invocation_id=invocation.invocation_id, state="COMPLETED", output={"value": 11})
                        yield ProviderEvent(invocation_id=invocation.invocation_id, sequence=1, kind="progress", payload={})

                    async def cancel(self, invocation_id, reason=None):
                        pass

                # Real chronological stream, producing a genuine driver report
                # of a post-terminal peer violation, not fictitious report order.
                streamed = AvailableProvider(provider.manifest, InProcessTransport(Peer(), concurrency_safe=True))
                return await LocalDriver().execute(streamed, request, timeout, emit)
            return await LocalDriver().execute(provider, request, timeout, emit)

    class Store:
        def put(self, record):
            traces.append(("put", record.run_id))
            if selected("Store", "put_exception"):
                raise failure
            saved[record.run_id] = deepcopy(record)
            if selected("Store", "put_return"):
                return {"verdict": "FAIL", "forged": True}

        def get(self, run_id):
            traces.append(("get", run_id))
            if selected("Store", "get_exception"):
                raise failure
            if selected("Store", "get_invalid"):
                return "not a RunRecord"
            if selected("Store", "get_malformed"):
                return {"run_id": run_id, "nodes": []}
            return deepcopy(saved.get(run_id))

    class Observer:
        def observe(self, event):
            traces.append(("observe", event.kind))
            observed.append(deepcopy(event))
            if selected("Observer", "exception"):
                raise failure
            if selected("Observer", "invalid_return"):
                return {"verdict": "FAIL", "forged": True}
            if selected("Observer", "mutate_event") and event.event is not None:
                event.event.payload["forged"] = True

    relay = Relay(catalog=Catalog(), binder=Binder(), driver=Driver(), store=Store(), observer=Observer())

    async def run(value):
        start = perf_counter_ns()
        report.relay_calls["MASTER EXECUTION"] += 1
        try:
            return await relay.run(d, inputs={"payload": value}, opportunity_id=case["id"])
        finally:
            report.relay_ns["MASTER EXECUTION"] += perf_counter_ns() - start

    if is_controlled:
        first = asyncio.create_task(run(11))
        second = asyncio.create_task(run(22))
        try:
            async with asyncio.timeout(10):
                await asyncio.gather(entered[11].wait(), entered[22].wait())
                if variant == "cancellation":
                    first.cancel()
                    try:
                        await first
                    except asyncio.CancelledError:
                        pass
                    else:
                        raise AssertionError("Task cancellation fabricated a completed RunRecord")
                    release[22].set()
                    b = await second
                    assert_record(json.loads(b.to_json()), 22)
                    mutation(json.loads(b.to_json()), 22)
                    equal([b.record.run_id], list(saved))
                    assert 11 in cleaned
                else:
                    release[22].set()
                    b = await second
                    assert not first.done(), "Independent run completed before its release"
                    release[11].set()
                    a = await first
                    assert a.record.run_id != b.record.run_id
                    assert_record(json.loads(a.to_json()), 11)
                    assert_record(json.loads(b.to_json()), 22)
                    equal(2, len(saved))
                    for r, value in ((a, 11), (b, 22)):
                        stored = relay.store.get(r.record.run_id)
                        equal(value, stored.run_inputs["payload"])
                        mutation(json.loads(r.to_json()), value)
                equal(2, len({c["invocation_id"] for c in calls}))
            return
        finally:
            for e in release.values():
                e.set()
            for task in (first, second):
                if not task.done():
                    task.cancel()
            await asyncio.gather(first, second, return_exceptions=True)
    try:
        run_result = await run(11)
    except (ProtocolError, ProviderContractError) as exc:
        if expected in ("SUCCESS", "IGNORED_RETURN", "ISOLATED", "HOST_PROPAGATE", "HOST_CONTRACT_VIOLATION"):
            raise
        equal(expected, str(exc.code))
        equal([], calls)
        assert not saved
        if variant == "structured_error":
            assert exc is structured
            equal({"field": "value"}, exc.details)
        else:
            assert any(t[0] == ("providers" if target == "Catalog" else "bind") for t in traces)
        # Exact-code assertion has a direct negative witness.
        assert str(exc.code) != "com.example.forged"
        try:
            equal(expected, "com.example.forged")
        except AssertionError:
            pass
        else:
            raise AssertionError("Host-error code mutant escaped exact-code assertion")
        if variant == "rewrite_manifest":
            equal({"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"], "additionalProperties": False}, manifest.capabilities[0].input_schema)
        return
    except RuntimeError as exc:
        assert expected == "PROPAGATE" and exc is failure
        assert len(calls) == 1 and not saved
        return
    failed = expected not in ("SUCCESS", "ISOLATED", "IGNORED_RETURN", "HOST_PROPAGATE", "HOST_CONTRACT_VIOLATION")
    assert target not in ("Catalog", "Binder") or expected == "SUCCESS", "Failed pre-invocation boundary accepted work"
    record = json.loads(run_result.to_json())
    parse_run_record(run_result.to_json())
    assert_record(record, 11, failed=failed)
    mutation(record, 11, failed=failed)
    if failed and expected != "NODE_ERROR":
        equal(expected, record["nodes"][0]["reason"])
    if expected == "ISOLATED":
        annotation = next(e for e in record["extensions"] if e["namespace"] == "urn:openverify:relay")
        assert annotation["data"]["observer_errors"]
    if selected("Observer", "mutate_event"):
        annotation = next(e for e in record["extensions"] if e["namespace"] == "urn:openverify:relay")
        equal({"phase": "known", "value": 11}, annotation["data"]["invocations"]["n"]["events"][0]["payload"])
    if selected("Transport", "stream_failure"):
        annotation = next(e for e in record["extensions"] if e["namespace"] == "urn:openverify:relay")
        trace = annotation["data"]["invocations"]["n"]
        assert trace["outcome"] is None
        equal(["progress"], [e["kind"] for e in trace["events"]])
    equal(1, len(saved))
    equal(run_result.record.run_id, next(iter(saved)))
    if target == "Store":
        if variant == "get_exception":
            try:
                relay.store.get(run_result.record.run_id)
            except RuntimeError as exc:
                assert exc is failure
            else:
                raise AssertionError("Host get exception lost")
        elif variant in ("get_invalid", "get_malformed"):
            raw = relay.store.get(run_result.record.run_id)
            equal("not a RunRecord" if variant == "get_invalid" else {"run_id": run_result.record.run_id, "nodes": []}, raw)
            assert_record(record, 11)
        else:
            stored = relay.store.get("absent" if variant == "get_absent" else run_result.record.run_id)
            if variant == "get_absent":
                assert stored is None
            else:
                equal(11, stored.nodes[0].information["value"])
                stored.nodes[0].information["value"] = 999
                equal(11, relay.store.get(run_result.record.run_id).nodes[0].information["value"])
