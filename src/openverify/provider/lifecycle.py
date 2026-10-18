"""Stateful validation only: no runner, provider selection, or execution engine."""

from copy import deepcopy
from dataclasses import dataclass
from typing import cast

from pydantic import JsonValue

from .model import Capability, InitializeRequest, Invocation, ProviderManifest
from .validation import (
    Instant,
    fail,
    parse_cancel_request,
    parse_invocation,
    parse_outcome,
    parse_provider_event,
    parse_provider_manifest,
    parse_provider_object,
    timestamp,
    validate_payload,
    wire_data,
)


def negotiate_contract_version(runner_versions: list[str], provider_versions: list[str]) -> str:
    version = next((v for v in runner_versions if v in provider_versions), None)
    if version != "0.1":
        fail("CONTRACT_VERSION_UNSUPPORTED", "No supported common contract version")
    assert version is not None
    return version


@dataclass
class _Attempt:
    invocation: Invocation
    capability: Capability
    sequence: int = 0
    cancelled: bool = False
    terminal: bool = False
    observed_at: Instant | None = None


class LifecycleValidator:
    def __init__(self, manifest: ProviderManifest):
        self._manifest = parse_provider_manifest(wire_data(manifest))
        self._request: InitializeRequest | None = None
        self._initialization_attempted = False
        self._attempts: dict[str, _Attempt] = {}
        self._seen: set[str] = set()

    def initialize(self, request: JsonValue) -> str:
        if self._initialization_attempted:
            fail("PROTOCOL_VIOLATION", "Initialization already attempted")
        self._initialization_attempted = True
        parsed = cast(InitializeRequest, parse_provider_object("initialize-request", request))
        version = negotiate_contract_version(
            parsed.supported_contract_versions, self._manifest.supported_contract_versions
        )
        self._request = deepcopy(parsed)
        return version

    def accept(self, data: JsonValue, *, now: str | None = None) -> None:
        if self._request is None:
            fail("PROTOCOL_VIOLATION", "Work before initialization")
        # Record even rejected attempt identities: no implicit retries/idempotency.
        if isinstance(data, dict) and isinstance(data.get("invocation_id"), str):
            identity = cast(str, data["invocation_id"])
            if identity in self._seen:
                fail("PROTOCOL_VIOLATION", "Invocation ID reused")
            self._seen.add(identity)
        invocation = deepcopy(parse_invocation(data))
        matches = [
            c for c in self._manifest.capabilities if c.capability_id == invocation.capability_id
        ]
        if not matches:
            fail("CAPABILITY_UNAVAILABLE", "Capability ID not advertised")
        capability = next(
            (c for c in matches if c.capability_version == invocation.capability_version), None
        )
        if capability is None:
            fail("CAPABILITY_VERSION_UNSUPPORTED", "Capability version not advertised")
        assert capability is not None
        assert self._request is not None
        if capability.vcp_version is not None and invocation.vcp_version != capability.vcp_version:
            fail("INVALID_INVOCATION", "Capability requires its declared VCP version")
        if invocation.vcp_version is not None and (
            invocation.vcp_version != "draft"
            or invocation.vcp_version not in self._manifest.supported_vcp_versions
            or invocation.vcp_version not in self._request.supported_vcp_versions
        ):
            fail("INVALID_INVOCATION", "No compatible VCP version")
        validate_payload(capability.input_schema, invocation.input, "INVALID_INPUT")
        validate_payload(capability.config_schema, invocation.config, "INVALID_CONFIG")
        if invocation.deadline is not None and not capability.lifecycle_features.deadlines:
            fail("INVALID_INVOCATION", "Deadline unsupported")
        attempt = _Attempt(invocation, capability)
        attempt.observed_at = self._observe(attempt, now)
        self._attempts[invocation.invocation_id] = attempt

    def _lookup(self, data: JsonValue, *, terminal_ok: bool = False) -> _Attempt:
        if not isinstance(data, dict) or not isinstance(data.get("invocation_id"), str):
            fail("PROTOCOL_VIOLATION", "Missing invocation correlation")
        assert isinstance(data, dict)
        attempt = self._attempts.get(cast(str, data["invocation_id"]))
        if attempt is None or (attempt.terminal and not terminal_ok):
            fail("PROTOCOL_VIOLATION", "Unknown or terminal invocation")
        assert attempt is not None
        return attempt

    def event(self, data: JsonValue) -> None:
        attempt = self._lookup(data)
        if (
            attempt.invocation.deadline is not None
            and attempt.observed_at is not None
            and attempt.observed_at >= timestamp(attempt.invocation.deadline)
        ):
            fail("PROTOCOL_VIOLATION", "Already-expired invocation cannot emit events")
        event = parse_provider_event(data)
        if not attempt.capability.lifecycle_features.streaming:
            fail("PROTOCOL_VIOLATION", "Streaming not advertised")
        if (attempt.sequence == 0 and event.sequence != 1) or event.sequence <= attempt.sequence:
            fail("PROTOCOL_VIOLATION", "Events must start at 1 and strictly increase")
        if (
            event.kind in ("evidence", "artifact", "resource_usage")
            and attempt.invocation.vcp_version != "draft"
        ):
            fail("INVALID_PROVIDER_OUTPUT", "VCP event without compatible VCP invocation")
        if (
            event.kind == "resource_usage"
            and not attempt.capability.lifecycle_features.resource_reporting
        ):
            fail("PROTOCOL_VIOLATION", "Resource reporting not advertised")
        attempt.sequence = event.sequence

    def cancel(self, data: JsonValue) -> None:
        attempt = self._lookup(data, terminal_ok=True)
        parse_cancel_request(data)
        if attempt.terminal:
            return
        if not attempt.capability.lifecycle_features.cancellation:
            fail("PROTOCOL_VIOLATION", "Running cancellation not supported")
        attempt.cancelled = True

    def _observe(self, attempt: _Attempt, now: str | None) -> Instant | None:
        if attempt.invocation.deadline is not None and now is None:
            fail("PROTOCOL_VIOLATION", "Deadline validation requires provider-clock now")
        observed = timestamp(now) if now is not None else None
        return observed

    def outcome(self, data: JsonValue, *, now: str | None = None) -> None:
        attempt = self._lookup(data)
        outcome = parse_outcome(data)
        observed = self._observe(attempt, now)
        if outcome.state == "CANCELLED" and not attempt.cancelled:
            fail("PROTOCOL_VIOLATION", "CANCELLED without runner cancellation")
        expired = (
            attempt.invocation.deadline is not None
            and observed is not None
            and (
                observed >= timestamp(attempt.invocation.deadline)
                or (
                    attempt.observed_at is not None
                    and attempt.observed_at >= timestamp(attempt.invocation.deadline)
                )
            )
        )
        if (outcome.state == "DEADLINE_EXCEEDED") != bool(expired):
            fail("PROTOCOL_VIOLATION", "Terminal state contradicts deadline observation")
        if outcome.state == "COMPLETED":
            validate_payload(
                attempt.capability.output_schema, outcome.output, "INVALID_PROVIDER_OUTPUT"
            )
        if outcome.resource_usage is not None and (
            attempt.invocation.vcp_version != "draft"
            or not attempt.capability.lifecycle_features.resource_reporting
        ):
            fail("INVALID_PROVIDER_OUTPUT", "Final usage not supported by invocation/capability")
        attempt.observed_at = observed
        attempt.terminal = True

    def reject(self, data: JsonValue) -> None:
        """Binding-only provisional acceptance removal on pre-work RPC rejection."""
        attempt = self._lookup(data)
        if attempt.sequence or attempt.cancelled:
            fail("PROTOCOL_VIOLATION", "Rejection after observable acceptance")
        del self._attempts[attempt.invocation.invocation_id]

    def finish(self) -> None:
        if self._request is None or any(not a.terminal for a in self._attempts.values()):
            fail("PROTOCOL_VIOLATION", "Uninitialized session or missing terminal Outcome")


def validate_lifecycle(trace: JsonValue) -> None:
    if not isinstance(trace, dict) or set(trace) != {"manifest", "initialize", "steps", "finish"}:
        fail("PROTOCOL_VIOLATION", "Malformed lifecycle trace")
    assert isinstance(trace, dict)
    validator = LifecycleValidator(parse_provider_manifest(trace["manifest"]))
    validator.initialize(trace["initialize"])
    steps = trace["steps"]
    if not isinstance(steps, list) or type(trace["finish"]) is not bool:
        fail("PROTOCOL_VIOLATION", "Malformed trace steps/finish")
    assert isinstance(steps, list)
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("action"), str):
            fail("PROTOCOL_VIOLATION", "Malformed trace step")
        assert isinstance(step, dict)
        action = step["action"]
        field = {
            "accept": "invocation",
            "event": "event",
            "cancel": "request",
            "outcome": "outcome",
        }.get(cast(str, action))
        if field is None or field not in step or set(step) - {"action", field, "now"}:
            fail("PROTOCOL_VIOLATION", "Unknown trace action/fields")
        assert field is not None
        now = step.get("now")
        if now is not None and not isinstance(now, str):
            fail("PROTOCOL_VIOLATION", "Trace now must be UTC string")
        if action == "accept":
            validator.accept(step[field], now=cast(str | None, now))
        elif action == "event":
            validator.event(step[field])
        elif action == "cancel":
            validator.cancel(step[field])
        else:
            validator.outcome(step[field], now=cast(str | None, now))
    if trace["finish"]:
        validator.finish()
