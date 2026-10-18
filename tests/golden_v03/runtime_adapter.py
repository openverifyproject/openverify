"""Actual Relay and real in-process Provider streams; never calculates expectations."""
import asyncio
from copy import deepcopy
import json
import time

from tests.golden_v02.adapters.public import manifest_for
from tests.golden_v03.record_oracle import audit, corruptions
from tests.golden_v03.target import BASE
from tools.golden_v02.compare import equal


class Observer:
    def __init__(self):
        self.events = []

    def observe(self, event):
        self.events.append(deepcopy(event))


class ScriptedProvider:
    def __init__(self, identity, operation, behavior, calls, controls=None):
        self.identity = identity
        self.specification = manifest_for(identity, operation)
        self.behavior = deepcopy(behavior)
        self.calls = calls
        self.controls = controls
        self.cancelled = []

    def manifest(self):
        return self.specification

    async def cancel(self, invocation_id, reason=None):
        self.cancelled.append((invocation_id, reason))

    async def invoke(self, invocation):
        from openverify.provider import Outcome, ProviderError, ProviderEvent
        self.calls.append({"provider_id": self.specification.provider_id,
            "invocation_id": invocation.invocation_id, "input": deepcopy(invocation.input),
            "config": deepcopy(invocation.config)})
        if self.controls is not None:
            await self.controls.enter(self.identity)
        b = self.behavior
        if b.get("raise"):
            raise RuntimeError("scripted invocation exception")
        if b.get("hang"):
            await asyncio.Event().wait()
        for i, event in enumerate(b.get("events", []), 1):
            yield ProviderEvent(invocation_id=invocation.invocation_id, sequence=i, **event)
        if b.get("invalid_event"):
            yield ProviderEvent(invocation_id=invocation.invocation_id, sequence=2,
                                kind="progress", payload={"message": "wrong first sequence"})
        if b.get("error"):
            terminal = Outcome(invocation_id=invocation.invocation_id, state="ERROR",
                               error=ProviderError(**b["error"]), resource_usage=b.get("usage", {}))
        else:
            terminal = Outcome(invocation_id=invocation.invocation_id, state="COMPLETED",
                               output=deepcopy(b.get("outputs", {})), resource_usage=b.get("usage", {}))
        yield terminal
        if b.get("duplicate_terminal"):
            yield terminal


class Barriers:
    """Independent overlap, join readiness, and Control scheduling: events only."""
    def __init__(self):
        self.started = {name: asyncio.Event() for name in ("D1", "D2", "E1", "E2", "E3", "C")}
        self.release = asyncio.Event()
        self.active = set()

    async def enter(self, name):
        if name in self.started:
            self.started[name].set()
        if name in ("D1", "D2", "E1"):
            self.active.add(name)
            await self.release.wait()
            self.active.remove(name)
        if name == "E2":
            assert not self.active, "join entered while predecessors are held"
        if name == "C":
            assert not self.active, "Control overlaps prior wave"


def prepare(case, definition, *, controls=None, timeout=2):
    from openverify import Relay
    from openverify.relay import RuntimeConfig
    from openverify.model import ProviderBinding
    from openverify.standard import standard_catalog
    s = deepcopy(case["scenario"])
    s["definition"] = json.loads((BASE / "master.json").read_text(encoding="utf-8"))
    catalog, calls, bindings = standard_catalog(), [], {}
    for n in s["definition"]["graph"]["nodes"]:
        if n["id"] not in s["behaviors"]:
            continue
        provider = ScriptedProvider(n["id"], n["operation"], s["behaviors"][n["id"]], calls, controls)
        catalog.register(provider, concurrency_safe=True)
        bindings[n["id"]] = ProviderBinding(provider_id=provider.specification.provider_id,
            provider_version="1", **n["operation"])
    for role, outcome in s["policies"].items():
        operation = s["definition"]["execution_policy"][role.lower()]["operation"]
        p = ScriptedProvider("policy_" + role.lower(), operation,
                             s.get("policy_behaviors", {}).get(role, {"outputs": outcome}), calls)
        catalog.register(p, concurrency_safe=True)
        bindings["policy:" + role] = ProviderBinding(provider_id=p.specification.provider_id,
                                                    provider_version="1", **operation)
    observer = Observer()
    relay = Relay(catalog=catalog, observer=observer,
                  config=RuntimeConfig(bindings=bindings, max_concurrency=8, timeout=timeout))
    return s, relay, calls, observer


async def invoke(relay, definition, inputs, report, **kwargs):
    start = time.perf_counter_ns()
    try:
        return await relay.run(definition, inputs=deepcopy(inputs), opportunity_id="golden.v03", **kwargs)
    finally:
        report.relay_ns["MASTER EXECUTION"] += time.perf_counter_ns() - start


async def execute(case, definition, report):
    from openverify import parse_run_record
    from openverify.errors import ProtocolError
    from openverify.provider import ProviderContractError
    controls = Barriers() if case["id"] == "master.concurrency.barriers" else None
    s, relay, calls, observer = prepare(case, definition, controls=controls)
    try:
        if controls is not None:
            task = asyncio.create_task(invoke(relay, definition, s["inputs"], report))
            try:
                async with asyncio.timeout(3):
                    await asyncio.gather(*(controls.started[n].wait() for n in ("D1", "D2", "E1")))
                    assert controls.active == {"D1", "D2", "E1"}
                    assert not controls.started["E2"].is_set()
                    assert not controls.started["C"].is_set()
                    controls.release.set()
                    run = await task
            finally:
                controls.release.set()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        else:
            run = await invoke(relay, definition, s["inputs"], report)
    except (ProtocolError, ProviderContractError) as exc:
        equal(case.get("error_code"), str(exc.code))
        assert not any(".p_policy_" not in c["provider_id"] for c in calls), calls
        if case.get("error_code") == "RUN_INPUT":
            assert not calls, "Invalid initial inputs invoked policies/providers"
        return
    assert "error_code" not in case, "Expected error; Relay created an occurrence"
    record = json.loads(run.to_json())
    parse_run_record(run.to_json())
    audit(record, s, calls)
    assert observer.events[0].kind == "run_started"
    assert observer.events[-1].kind == "run_completed"
    for n in record["nodes"]:
        events = [e.kind for e in observer.events if e.node_id == n["node_id"] and e.kind != "provider_event"]
        equal(["node_terminal"] if n["state"] == "NONEXECUTED" else ["node_started", "node_terminal"], events)
    invocation_ids = [c["invocation_id"] for c in calls]
    assert len(invocation_ids) == len(set(invocation_ids))
    if case["id"] == "master.usage.final_authoritative":
        d1_events = [e.event for e in observer.events if e.node_id == "D1" and e.kind == "provider_event"]
        equal(["resource_usage", "evidence"], [e.kind for e in d1_events])
        equal([1, 2], [e.sequence for e in d1_events])
        d1 = next(n for n in record["nodes"] if n["node_id"] == "D1")
        equal([{"message": "observed evidence"}], d1["observation"]["evidence"])
    if case["id"] == "master.normal":
        for name, corrupted in corruptions(record):
            try:
                audit(corrupted, s, calls)
            except AssertionError:
                continue
            raise AssertionError("Trusted-script oracle missed corruption: " + name)


async def exceptional(case, definition, report):
    """Fixed master also exposes cancellation, timeout, and cross-run isolation."""
    from openverify.lifecycle import Cancellation
    # Definition is the same canonical master; only script/host stimuli change.
    stimuli = deepcopy(next(c for c in json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
                            if c["id"] == "master.normal"))
    if case["id"] == "master.timeout":
        stimuli["scenario"]["behaviors"]["D1"]["hang"] = True
        s, relay, calls, observer = prepare(stimuli, definition, timeout=0.02)
        run = await invoke(relay, definition, s["inputs"], report)
        n = next(n for n in run.record.nodes if n.node_id == "D1")
        assert n.state == "ERROR" and n.reason == "TIMEOUT"
        assert not n.information and n.result.verdict is None
        downstream = next(n for n in run.record.nodes if n.node_id == "E2")
        assert downstream.state == "NONEXECUTED" and downstream.reason == "INPUT_UNAVAILABLE"
        s["nodes"] = deepcopy(next(c["scenario"]["nodes"] for c in
            json.loads((BASE / "scenarios.json").read_text(encoding="utf-8")) if c["id"] == "master.fault.exception"))
        s["nodes"]["D1"]["reason"] = "TIMEOUT"
        audit(json.loads(run.to_json()), s, calls)
    elif case["id"] == "master.running_cancellation":
        stimuli["scenario"]["behaviors"]["D1"]["hang"] = True
        entered = asyncio.Event()

        class Entry:
            async def enter(self, identity):
                if identity == "D1":
                    entered.set()

        s, relay, calls, observer = prepare(stimuli, definition, controls=Entry())
        token = Cancellation()
        task = asyncio.create_task(invoke(relay, definition, s["inputs"], report, cancellation=token))
        try:
            async with asyncio.timeout(3):
                await entered.wait()
                token.cancel("Cancel after entering provider")
                run = await task
            assert run.record.nodes[0].node_id == "D1"
            assert run.record.nodes[0].state == "CANCELLED"
            assert run.record.cancellation.phase == "RUNNING"
            assert not run.record.nodes[0].information
            assert all(n.state == "NONEXECUTED" and n.result.disposition == "CANCELLED" for n in run.record.nodes[1:])
            s["nodes"] = cancelled_facts(s, running=True)
            audit(json.loads(run.to_json()), s, calls)
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    else:
        s, relay, calls, observer = prepare(stimuli, definition)
        token = Cancellation()
        token.cancel("Only this run")
        first, second = await asyncio.gather(
            invoke(relay, definition, s["inputs"], report, cancellation=token),
            invoke(relay, definition, {**s["inputs"], "payload": 19}, report))
        assert first.record.run_id != second.record.run_id
        assert all(n.state == "NONEXECUTED" and n.result.disposition == "CANCELLED" for n in first.record.nodes)
        assert not first.record.provider_bindings
        assert first.record.cancellation.phase == "BEFORE_START"
        assert all(n.state == "SUCCESS" for n in second.record.nodes)
        equal({"value": 5}, next(n.information for n in second.record.nodes if n.node_id == "D1"))
        equal(19, next(n.input_values["run"] for n in second.record.nodes if n.node_id == "D1"))
        first_s = deepcopy(s)
        first_s["nodes"] = cancelled_facts(first_s)
        audit(json.loads(first.to_json()), first_s, calls[:3])
        second_s = deepcopy(s)
        second_s["inputs"]["payload"] = 19
        audit(json.loads(second.to_json()), second_s, calls[3:])


def cancelled_facts(scenario, running=False):
    return {n["id"]: {"state": "CANCELLED" if running and n["id"] == "D1" else "NONEXECUTED",
        "reason": "CANCELLATION", "information": {}, "result": {"protocol": "draft",
        "disposition": "CANCELLED", "output": {"reason": "CANCELLATION"}}}
        for n in scenario["definition"]["graph"]["nodes"]}


async def policy_fault(case, definition, report):
    from openverify.errors import ProtocolError
    from openverify.provider import ProviderContractError
    stimuli = deepcopy(next(c for c in json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
                            if c["id"] == "master.normal"))
    role = case["role"]
    behavior = {"raise": True} if case["fault"] == "exception" else {"error": {
        "code": "com.example.policy_failed", "message": "scripted"}}
    stimuli["scenario"]["policy_behaviors"] = {role: behavior}
    s, relay, calls, observer = prepare(stimuli, definition)
    try:
        await invoke(relay, definition, s["inputs"], report)
    except (ProtocolError, ProviderContractError) as exc:
        equal(case["error_code"], str(exc.code))
        roles = ["ACTIVATION", "SELECTION", "ADMISSION"]
        equal(["com.example.golden.p_policy_" + r.lower() for r in roles[:roles.index(role) + 1]],
              [c["provider_id"] for c in calls])
        return
    raise AssertionError("Policy failure created an occurrence")
