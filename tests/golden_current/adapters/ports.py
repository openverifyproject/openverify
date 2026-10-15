"""Replacement objects exercise all six public ports through complete runs."""

from __future__ import annotations

from copy import deepcopy

from tests.golden_current.adapters.public import ScriptedTransport, manifest_for, prepare
from tests.golden_current.adapters.runtime import basic
from tools.golden.compare import equal


async def experiment(payload):
    from openverify.provider import Outcome
    from openverify.relay.ports import AvailableProvider, InvocationReport

    name, variant = payload["port"], payload["variant"]
    sc = basic()
    req = sc["definition"]["graph"]["nodes"][0]["operation"]
    calls = []
    observations = []
    saved = {}
    manifest = manifest_for("a", req)
    transport = ScriptedTransport({"outputs": {"value": "a"}}, calls)
    original = AvailableProvider(manifest, transport)
    bad_manifest = manifest_for(
        "incompatible", {"capability_id": "com.example.other", "capability_version": "1"}
    )
    incompatible = AvailableProvider(bad_manifest, transport)
    replacement_calls = []

    class ReplacementCatalog:
        def providers(self):
            replacement_calls.append("providers")
            if variant == "exception":
                raise RuntimeError("golden catalog failure")
            if variant == "invalid":
                return (object(),)
            return (original,)

    class ReplacementBinder:
        def bind(self, requirement, providers, explicit=None):
            replacement_calls.append("bind")
            equal(req["capability_id"], requirement.capability_id)
            if variant == "exception":
                raise RuntimeError("golden binder failure")
            if variant == "invalid":
                return incompatible
            return next(p for p in providers if p.manifest.provider_id == manifest.provider_id)

    class ReplacementDriver:
        async def execute(self, provider, request, timeout, emit):
            replacement_calls.append("execute")
            assert timeout > 0
            if variant == "exception":
                raise RuntimeError("golden driver failure")
            if variant == "invalid":
                return InvocationReport(
                    Outcome(
                        invocation_id="substituted", state="COMPLETED", output={"value": "forged"}
                    )
                )
            events = []

            def event(e):
                events.append(e)
                emit(e)

            outcome = await provider.transport.invoke(request, event)
            return InvocationReport(outcome, tuple(events))

    class ReplacementTransport:
        async def invoke(self, request, emit):
            replacement_calls.append("invoke")
            if variant == "exception":
                raise RuntimeError("golden transport failure")
            if variant == "invalid":
                return Outcome(
                    invocation_id="substituted", state="COMPLETED", output={"value": "forged"}
                )
            return await transport.invoke(request, emit)

    class ReplacementStore:
        def put(self, record):
            replacement_calls.append("put")
            if variant == "exception":
                raise RuntimeError("golden store failure")
            saved[record.run_id] = deepcopy(record)

        def get(self, run_id):
            replacement_calls.append("get")
            if variant == "invalid":
                return {"run_id": run_id, "fabricated": True}
            return deepcopy(saved.get(run_id))

    class ReplacementObserver:
        def observe(self, event):
            replacement_calls.append("observe")
            observations.append(deepcopy(event))
            if variant == "exception":
                raise RuntimeError("golden observer failure")
            if variant == "invalid":
                return {"verdict": "FAIL", "run_id": "forged"}
            return None

    replacements = {}
    transports = {}
    if variant != "default":
        if name == "ProviderCatalog":
            replacements["catalog"] = ReplacementCatalog()
        if name == "ProviderBinder":
            replacements["binder"] = ReplacementBinder()
        if name == "ExecutionDriver":
            replacements["driver"] = ReplacementDriver()
        if name == "ProviderTransport":
            transports["a"] = ReplacementTransport()
        if name == "RecordStore":
            replacements["store"] = ReplacementStore()
        if name == "EventObserver":
            replacements["observer"] = ReplacementObserver()
    bound = prepare(sc, replacements=replacements, transports=transports)
    rejected = variant in ("invalid", "exception") and name not in ("EventObserver", "RecordStore")
    try:
        record = await bound.invoke()
    except Exception as exc:
        if name == "RecordStore" and variant == "exception":
            assert "golden store failure" in str(exc)
            return {"verified": True, "store_failure_propagated": True}
        assert rejected, (name, variant, exc)
        return {
            "verified": True,
            "rejection": getattr(exc, "code", type(exc).__name__),
            "calls": replacement_calls,
        }
    if rejected:
        equal("ERROR", record["nodes"][0]["state"])
        equal({}, record["nodes"][0]["information"])
    else:
        equal("SUCCESS", record["nodes"][0]["state"])
        equal({"value": "a"}, record["nodes"][0]["information"])
    if variant != "default":
        assert replacement_calls, "replacement was never called"
    if name == "RecordStore":
        retained = bound.relay.store.get(record["run_id"])
        if variant == "invalid":
            # A deliberately corrupt store response must not be advertised as a
            # RunRecord. This test is allowed to reveal an enforcement gap.
            from openverify import parse_run_record

            try:
                parse_run_record(retained)
            except Exception:
                pass
            else:
                raise AssertionError("corrupt store response accepted as RunRecord")
        else:
            assert retained is not None
            equal(record["run_id"], retained.run_id)
            retained.information if hasattr(retained, "information") else None
            retained.nodes[0].information["value"] = "tampered-copy"
            equal("a", bound.relay.store.get(record["run_id"]).nodes[0].information["value"])
    if name == "EventObserver" and variant == "exception":
        assert "golden observer failure" in str(record.get("extensions", [])), (
            "observer diagnostics missing"
        )
    if variant == "isolation":
        another = await bound.invoke(opportunity="golden.second")
        assert record["run_id"] != another["run_id"]
        equal({"value": "a"}, another["nodes"][0]["information"])
    return {"verified": True, "calls": replacement_calls}
