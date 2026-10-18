"""Thin public Python / Provider Contract adapter.

All imports of OpenVerify are invocation/construction operations. No validator,
resolver, reducer or runtime helper is used to calculate an expected answer.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache


def wire(value):
    from openverify import serialize

    return json.loads(serialize(value))


def provider_id(identity):
    return "com.example.golden.p_" + re.sub("[^a-z0-9_]", "_", identity.lower())


@dataclass
class BoundRun:
    relay: object
    definition: dict
    inputs: dict
    calls: list
    providers: dict

    async def invoke(self, *, cancellation=None, opportunity="golden.opportunity"):
        result = await self.relay.run(
            json.dumps(self.definition, ensure_ascii=False),
            inputs=deepcopy(self.inputs),
            opportunity_id=opportunity,
            cancellation=cancellation,
        )
        return json.loads(result.to_json())


class ScriptedTransport:
    """Conformance double implements the actual public ProviderTransport port."""

    def __init__(self, behavior, calls, *, entered=None, release=None, callback=None):
        self.behavior = deepcopy(behavior)
        self.calls = calls
        self.entered, self.release, self.callback = entered, release, callback

    async def invoke(self, request, emit):
        from openverify.provider import Outcome, ProviderEvent, ProviderError

        invocation = request.invocation
        self.calls.append(
            {
                "provider_id": request.manifest.provider_id,
                "capability_id": invocation.capability_id,
                "invocation_id": invocation.invocation_id,
                "input": deepcopy(invocation.input),
                "config": deepcopy(invocation.config),
            }
        )
        if self.entered:
            self.entered.set()
        if self.callback:
            await self.callback(request)
        if self.release:
            await self.release.wait()
        b = self.behavior
        if b.get("raise"):
            raise RuntimeError(b["raise"])
        for i, event in enumerate(b.get("events", []), 1):
            emit(ProviderEvent(invocation_id=invocation.invocation_id, sequence=i, **event))
        if b.get("usage"):
            emit(
                ProviderEvent(
                    invocation_id=invocation.invocation_id,
                    sequence=len(b.get("events", [])) + 1,
                    kind="resource_usage",
                    payload=b["usage"],
                )
            )
        if "error" in b:
            return Outcome(
                invocation_id=invocation.invocation_id,
                state="ERROR",
                error=ProviderError(**b["error"]),
                resource_usage=b.get("usage", {}),
            )
        return Outcome(
            invocation_id=invocation.invocation_id,
            state="COMPLETED",
            output=deepcopy(b.get("outputs", {})),
            resource_usage=b.get("usage", {}),
        )


def manifest_for(
    identity, requirement, *, input_schema=True, output_schema=True, config_schema=True
):
    """Construction only; schemas describe the simulator, not expected outcomes."""
    from openverify.provider import ProviderManifest

    return ProviderManifest.model_validate(
        {
            "provider_id": provider_id(identity),
            "provider_version": "1",
            "supported_contract_versions": ["0.1"],
            "supported_vcp_versions": ["draft"],
            "capabilities": [
                {
                    "capability_id": requirement["capability_id"],
                    "capability_version": requirement["capability_version"],
                    "input_schema": input_schema,
                    "output_schema": output_schema,
                    "config_schema": config_schema,
                    "vcp_version": "draft",
                    "lifecycle_features": {
                        "streaming": True,
                        "cancellation": True,
                        "deadlines": False,
                        "resource_reporting": True,
                    },
                }
            ],
        }
    )


def prepare(
    scenario, *, replacements=None, standard=True, transports=None, max_concurrency=8, timeout=5
):
    from openverify import Relay
    from openverify.model import ProviderBinding
    from openverify.relay import RuntimeConfig
    from openverify.relay.adapters.catalog import Catalog
    from openverify.standard import standard_catalog

    d = deepcopy(scenario["definition"])
    calls = []
    providers = {}
    bindings = {}
    catalog = standard_catalog() if standard else Catalog()
    for n in d["graph"]["nodes"]:
        if n["operation"]["capability_id"] == "openverify.aggregate" and n[
            "id"
        ] not in scenario.get("behaviors", {}):
            continue
        b = scenario.get("behaviors", {}).get(n["id"], {})
        manifest = manifest_for(n["id"], n["operation"], **b.get("contract_schemas", {}))
        transport = (transports or {}).get(n["id"]) or ScriptedTransport(b, calls)
        catalog.register_transport(manifest, transport)
        providers[n["id"]] = (manifest, transport)
        bindings[n["id"]] = ProviderBinding(
            provider_id=manifest.provider_id,
            provider_version=manifest.provider_version,
            **n["operation"],
        )
    # Custom policy declarations are adapter-side construction of public inputs;
    # their exact outcome objects were independently frozen in Stage A.
    for role, outcome in scenario.get("policies", {}).items():
        requirement = {
            "capability_id": "com.example.golden.policy_" + role.lower(),
            "capability_version": "1",
        }
        key = "policy:" + role
        assert d["execution_policy"][role.lower()]["operation"] == requirement
        manifest = manifest_for("policy_" + role.lower(), requirement)
        transport = ScriptedTransport(
            scenario.get("policy_behaviors", {}).get(role, {"outputs": outcome}), calls
        )
        catalog.register_transport(manifest, transport)
        bindings[key] = ProviderBinding(
            provider_id=manifest.provider_id, provider_version="1", **requirement
        )
    kwargs = dict(replacements or {})
    kwargs.setdefault("catalog", catalog)
    kwargs.setdefault(
        "config", RuntimeConfig(bindings=bindings, max_concurrency=max_concurrency, timeout=timeout)
    )
    return BoundRun(Relay(**kwargs), d, scenario.get("inputs", {}), calls, providers)


async def run_scenario(scenario):
    prepared = prepare(scenario)
    record = await prepared.invoke()
    return {"record": record, "calls": prepared.calls, "definition": prepared.definition}


def parse(operation, payload):
    from openverify import parse_definition, parse_result, flattened_status
    from openverify.validation import parse_object

    if operation == "parse_definition":
        return {"value": wire(parse_definition(payload))}
    if operation == "parse_result":
        value = parse_result(payload)
        try:
            status = flattened_status(value)
            error = None
        except Exception as exc:
            status = None
            error = getattr(exc, "code", type(exc).__name__)
        return {"value": wire(value), "projection": status, "projection_error": error}
    if operation == "parse_raw":
        return {"value": wire(parse_object(payload["object_type"], payload["raw"]))}
    return {"value": wire(parse_object(payload["object_type"], payload["value"]))}


def provider_trace(payload):
    from openverify.provider import validate_lifecycle

    validate_lifecycle(deepcopy(payload))
    return {"accept": True}


def provider_frame(payload):
    from openverify.provider.stdio import FrameDecoder

    raw = bytes.fromhex(payload["hex"])
    decoder = FrameDecoder()
    messages = []
    # One-byte chunks exercise partial header/body boundaries without timing.
    for b in raw:
        messages.extend(decoder.feed(bytes([b])))
    decoder.finish()
    return {"messages": messages}


@lru_cache(maxsize=1)
def reducer_provider():
    """One public catalog fixture; each case still sends a fresh invocation."""
    from openverify.standard import standard_catalog

    return next(
        p
        for p in standard_catalog().providers()
        if any(c.capability_id == "openverify.aggregate" for c in p.manifest.capabilities)
    )


async def reducer(payload):
    """Invoke the shipped reducer through its advertised Provider Contract port.

    Standalone nonexecution Results cannot be emitted by an invoked graph
    evaluator. Direct Contract invocation is necessary for that interchange space.
    Graph execution cases independently cover authored membership and Control.
    """
    from openverify.provider import Invocation
    from openverify.relay.ports import InvocationRequest

    selected = reducer_provider()
    names = ["member_" + str(i) for i in range(len(payload["members"]))]
    inputs = {
        **dict(zip(names, deepcopy(payload["members"]))),
        "members": names,
        "subject": {
            "id": "golden.subject",
            "type": "application/json",
            "locator": {"host_supplied": True},
        },
        "criterion": {
            "id": "golden.criterion",
            "description": "The explicitly supplied deterministic criterion holds",
        },
    }
    config = deepcopy(payload["config"])
    if "weights" in config:
        config["weights"] = dict(zip(names, config["weights"]))
    invocation = Invocation(
        invocation_id="golden.reducer",
        contract_version="0.1",
        capability_id="openverify.aggregate",
        capability_version="1",
        vcp_version="draft",
        input=inputs,
        config=config,
    )
    events = []
    outcome = await selected.transport.invoke(
        InvocationRequest(selected.manifest, invocation), events.append
    )
    from openverify.provider import wire_data

    return {"outcome": wire_data(outcome), "events": [wire_data(e) for e in events]}
