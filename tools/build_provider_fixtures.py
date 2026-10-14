"""Portable targeted cases derived from Provider Contract prose."""

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "provider-contract/conformance"
CAPABILITY = {
    "capability_id": "com.example.execution.echo",
    "capability_version": "1",
    "input_schema": {"type": "string"},
    "output_schema": {"type": "string"},
    "config_schema": {"type": "object", "additionalProperties": False},
    "lifecycle_features": {
        "streaming": True,
        "cancellation": True,
        "deadlines": True,
        "resource_reporting": True,
    },
}
MANIFEST = {
    "provider_id": "com.example.provider.echo",
    "provider_version": "1",
    "supported_contract_versions": ["0.1"],
    "supported_vcp_versions": ["draft"],
    "capabilities": [CAPABILITY],
}
INITIALIZE = {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]}
INVOCATION = {
    "invocation_id": "attempt-1",
    "contract_version": "0.1",
    "capability_id": CAPABILITY["capability_id"],
    "capability_version": "1",
    "input": "hello",
    "config": {},
    "vcp_version": "draft",
}
EVENT = {
    "invocation_id": "attempt-1",
    "sequence": 1,
    "kind": "progress",
    "payload": {"phase": "working"},
}
OUTCOME = {"invocation_id": "attempt-1", "state": "COMPLETED", "output": "hello"}
USAGE = {"custom.calls": {"unit": "call", "kind": "EXACT", "value": 1}}
CANCEL = {"invocation_id": "attempt-1", "reason": "runner stopping"}
BEFORE = "2026-10-13T00:00:00Z"
DEADLINE = "2026-10-13T00:00:01Z"
cases = []


def add(identity, object_type, value, error=None, spec="wire-format.md"):
    valid = error is None
    folder = "valid" if valid else "invalid"
    case = {
        "id": identity,
        "object_type": object_type,
        "input": f"{folder}/{identity}.json",
        "valid": valid,
        "expected": f"expected/{identity}.json",
        "spec": f"../spec/draft/{spec}",
    }
    expected = {"valid": valid}
    if error:
        case["error_code"] = error
        expected["error_code"] = error
    for relative, data in ((case["input"], value), (case["expected"], expected)):
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    cases.append(case)


def step(action, value, now=None):
    field = {"accept": "invocation", "event": "event", "outcome": "outcome", "cancel": "request"}[
        action
    ]
    return {"action": action, field: value, **({"now": now} if now else {})}


def trace(*steps, manifest=MANIFEST, initialize=INITIALIZE, finish=True):
    return deepcopy(
        {"manifest": manifest, "initialize": initialize, "steps": list(steps), "finish": finish}
    )


def lifecycle(identity, steps, error=None, **kwargs):
    add(identity, "lifecycle", trace(*steps, **kwargs), error, "lifecycle.md")


add(
    "minimal-manifest",
    "provider-manifest",
    {**MANIFEST, "capabilities": [], "supported_vcp_versions": []},
)
add(
    "multi-capability-manifest",
    "provider-manifest",
    {
        **MANIFEST,
        "capabilities": [
            CAPABILITY,
            {**CAPABILITY, "capability_id": "com.example.policy.evaluate"},
            {**CAPABILITY, "capability_version": "2"},
        ],
    },
)
add("capability", "capability", CAPABILITY)
add("invocation", "invocation", INVOCATION)
add(
    "context-and-budget",
    "invocation",
    {**INVOCATION, "context": {"reference": "opaque"}, "resource_budget": USAGE},
)
add("progress-event", "provider-event", EVENT)
add(
    "evidence-event",
    "provider-event",
    {**EVENT, "kind": "evidence", "payload": {"structured_data": {"observed": "SAT"}}},
)
add(
    "artifact-event",
    "provider-event",
    {
        **EVENT,
        "kind": "artifact",
        "payload": {"id": "a", "type": "text/plain", "locator": "opaque"},
    },
)
add("usage-event", "provider-event", {**EVENT, "kind": "resource_usage", "payload": USAGE})
add("diagnostic-event", "provider-event", {**EVENT, "kind": "diagnostic", "payload": "waiting"})
add(
    "extension-event",
    "provider-event",
    {
        **EVENT,
        "kind": "extension",
        "payload": {"namespace": "com.example.observation", "data": [None, True, 1]},
    },
)
add("cancel-request", "cancel-request", CANCEL)
add("completed-outcome", "outcome", OUTCOME)
add("null-output", "outcome", {**OUTCOME, "output": None})
add(
    "error-outcome",
    "outcome",
    {
        "invocation_id": "attempt-1",
        "state": "ERROR",
        "error": {"code": "com.example.tool_failed", "message": "Tool exited", "details": None},
    },
)
add("cancelled-outcome", "outcome", {"invocation_id": "attempt-1", "state": "CANCELLED"})
add("deadline-outcome", "outcome", {"invocation_id": "attempt-1", "state": "DEADLINE_EXCEEDED"})
add(
    "extension-roundtrip",
    "provider-manifest",
    {**MANIFEST, "extensions": {"com.example.future": {"nested": [None, False, 0, 1.5, "é", {}]}}},
)
add("initialize-request", "initialize-request", INITIALIZE)
add("initialize-result", "initialize-result", {"contract_version": "0.1", "manifest": MANIFEST})
add("contract-error", "provider-error", {"code": "INVALID_INPUT", "message": "Rejected"})
add("integral-sequence", "provider-event", {**EVENT, "sequence": 1.0})

accept = step("accept", INVOCATION)
event = step("event", EVENT)
outcome = step("outcome", OUTCOME)
cancel = step("cancel", CANCEL)
lifecycle("successful-invocation", [accept, outcome])
lifecycle(
    "invocation-with-events", [accept, event, step("event", {**EVENT, "sequence": 3}), outcome]
)
lifecycle(
    "evidence-and-usage",
    [
        accept,
        step("event", {**EVENT, "kind": "evidence", "payload": {"message": "observation"}}),
        step("event", {**EVENT, "sequence": 2, "kind": "resource_usage", "payload": USAGE}),
        step("outcome", {**OUTCOME, "resource_usage": USAGE}),
    ],
)
lifecycle(
    "cooperative-cancel",
    [accept, cancel, step("outcome", {"invocation_id": "attempt-1", "state": "CANCELLED"}), cancel],
)
lifecycle("completion-wins-cancel", [accept, cancel, outcome])
lifecycle(
    "deadline-expiry",
    [
        step("accept", {**INVOCATION, "deadline": DEADLINE}, BEFORE),
        step("outcome", {"invocation_id": "attempt-1", "state": "DEADLINE_EXCEEDED"}, DEADLINE),
    ],
)
lifecycle(
    "already-expired",
    [
        step("accept", {**INVOCATION, "deadline": BEFORE}, DEADLINE),
        step("outcome", {"invocation_id": "attempt-1", "state": "DEADLINE_EXCEEDED"}, DEADLINE),
    ],
)
lifecycle("running-prefix", [accept, event], finish=False)
lifecycle(
    "interleaved-invocations",
    [
        accept,
        step("accept", {**INVOCATION, "invocation_id": "attempt-2"}),
        step("event", {**EVENT, "invocation_id": "attempt-2"}),
        event,
        outcome,
        step("outcome", {**OUTCOME, "invocation_id": "attempt-2"}),
    ],
)

add(
    "unsupported-contract",
    "invocation",
    {**INVOCATION, "contract_version": "1.0"},
    "CONTRACT_VERSION_UNSUPPORTED",
)
add(
    "malformed-capability",
    "capability",
    {**CAPABILITY, "lifecycle_features": {"streaming": True}},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "duplicate-capability",
    "provider-manifest",
    {**MANIFEST, "capabilities": [CAPABILITY, CAPABILITY]},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "bad-namespace",
    "capability",
    {**CAPABILITY, "capability_id": "verifier.smt"},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "invalid-schema",
    "capability",
    {**CAPABILITY, "input_schema": {"type": "not-a-type"}},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "external-schema",
    "capability",
    {**CAPABILITY, "input_schema": {"$ref": "https://example.com/schema"}},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "unknown-core-field",
    "invocation",
    {**INVOCATION, "mandatory_extension": True},
    "INVALID_INVOCATION",
)
add("invalid-invocation", "invocation", {**INVOCATION, "invocation_id": ""}, "INVALID_INVOCATION")
add(
    "invalid-deadline",
    "invocation",
    {**INVOCATION, "deadline": "2026-02-30T00:00:00Z"},
    "INVALID_INVOCATION",
)
add(
    "non-utc-deadline",
    "invocation",
    {**INVOCATION, "deadline": "2026-10-13T00:00:00-07:00"},
    "INVALID_INVOCATION",
)
add(
    "empty-evidence",
    "provider-event",
    {**EVENT, "kind": "evidence", "payload": {}},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "invalid-resource-range",
    "provider-event",
    {
        **EVENT,
        "kind": "resource_usage",
        "payload": {"x": {"unit": "u", "kind": "RANGE", "minimum": 2, "maximum": 1}},
    },
    "INVALID_PROVIDER_OUTPUT",
)
add("bool-sequence", "provider-event", {**EVENT, "sequence": True}, "INVALID_PROVIDER_OUTPUT")
add(
    "bool-resource",
    "provider-event",
    {
        **EVENT,
        "kind": "resource_usage",
        "payload": {"x": {"unit": "u", "kind": "EXACT", "value": True}},
    },
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "malformed-outcome",
    "outcome",
    {"invocation_id": "attempt-1", "state": "COMPLETED"},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "error-as-fail",
    "outcome",
    {
        "invocation_id": "attempt-1",
        "state": "FAIL",
        "error": {"code": "com.example.failed", "message": "failed"},
    },
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "error-with-verdict",
    "outcome",
    {
        "invocation_id": "attempt-1",
        "state": "ERROR",
        "verdict": "FAIL",
        "error": {"code": "com.example.failed", "message": "failed"},
    },
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "completed-with-error",
    "outcome",
    {**OUTCOME, "error": {"code": "INVALID_INPUT", "message": "bad"}},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "unknown-error-code",
    "provider-error",
    {"code": "TOOL_FAILED", "message": "failed"},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "null-optional-field",
    "cancel-request",
    {"invocation_id": "attempt-1", "reason": None},
    "PROTOCOL_VIOLATION",
)
lifecycle(
    "no-common-contract",
    [],
    "CONTRACT_VERSION_UNSUPPORTED",
    initialize={**INITIALIZE, "supported_contract_versions": ["0.2"]},
)
lifecycle(
    "unsupported-capability",
    [step("accept", {**INVOCATION, "capability_id": "com.example.missing"})],
    "CAPABILITY_UNAVAILABLE",
)
lifecycle(
    "unsupported-capability-version",
    [step("accept", {**INVOCATION, "capability_version": "2"})],
    "CAPABILITY_VERSION_UNSUPPORTED",
)
lifecycle("invalid-input", [step("accept", {**INVOCATION, "input": 1})], "INVALID_INPUT")
lifecycle(
    "invalid-config", [step("accept", {**INVOCATION, "config": {"unknown": 1}})], "INVALID_CONFIG"
)
lifecycle(
    "invalid-completed-output",
    [accept, step("outcome", {**OUTCOME, "output": False})],
    "INVALID_PROVIDER_OUTPUT",
)
lifecycle(
    "wrong-outcome-correlation",
    [accept, step("outcome", {**OUTCOME, "invocation_id": "other"})],
    "PROTOCOL_VIOLATION",
)
lifecycle("unknown-event", [event], "PROTOCOL_VIOLATION")
lifecycle(
    "wrong-event-correlation",
    [accept, step("event", {**EVENT, "invocation_id": "other"})],
    "PROTOCOL_VIOLATION",
)
lifecycle(
    "sequence-not-one", [accept, step("event", {**EVENT, "sequence": 2})], "PROTOCOL_VIOLATION"
)
lifecycle("nonmonotonic-sequence", [accept, event, event], "PROTOCOL_VIOLATION")
lifecycle(
    "decreasing-sequence",
    [
        accept,
        event,
        step("event", {**EVENT, "sequence": 3}),
        step("event", {**EVENT, "sequence": 2}),
    ],
    "PROTOCOL_VIOLATION",
)
lifecycle("duplicate-outcome", [accept, outcome, outcome], "PROTOCOL_VIOLATION")
lifecycle("event-after-terminal", [accept, outcome, event], "PROTOCOL_VIOLATION")
lifecycle("missing-outcome", [accept], "PROTOCOL_VIOLATION")
lifecycle("duplicate-invocation", [accept, accept], "PROTOCOL_VIOLATION")
lifecycle(
    "unsolicited-cancelled",
    [accept, step("outcome", {"invocation_id": "attempt-1", "state": "CANCELLED"})],
    "PROTOCOL_VIOLATION",
)
lifecycle("unknown-cancel", [cancel], "PROTOCOL_VIOLATION")
lifecycle(
    "early-deadline-state",
    [
        step("accept", {**INVOCATION, "deadline": DEADLINE}, BEFORE),
        step("outcome", {"invocation_id": "attempt-1", "state": "DEADLINE_EXCEEDED"}, BEFORE),
    ],
    "PROTOCOL_VIOLATION",
)
lifecycle(
    "late-completion",
    [
        step("accept", {**INVOCATION, "deadline": DEADLINE}, BEFORE),
        step("outcome", OUTCOME, DEADLINE),
    ],
    "PROTOCOL_VIOLATION",
)
lifecycle(
    "vcp-unavailable",
    [accept],
    "INVALID_INVOCATION",
    initialize={**INITIALIZE, "supported_vcp_versions": []},
)
lifecycle(
    "evidence-without-vcp",
    [
        step("accept", {k: v for k, v in INVOCATION.items() if k != "vcp_version"}),
        step("event", {**EVENT, "kind": "evidence", "payload": {"message": "observation"}}),
    ],
    "INVALID_PROVIDER_OUTPUT",
)
for feature, steps, code in (
    ("streaming", [accept, event], "PROTOCOL_VIOLATION"),
    ("cancellation", [accept, cancel], "PROTOCOL_VIOLATION"),
    (
        "deadlines",
        [step("accept", {**INVOCATION, "deadline": DEADLINE}, BEFORE)],
        "INVALID_INVOCATION",
    ),
    (
        "resource_reporting",
        [accept, step("outcome", {**OUTCOME, "resource_usage": USAGE})],
        "INVALID_PROVIDER_OUTPUT",
    ),
):
    manifest = deepcopy(MANIFEST)
    manifest["capabilities"][0]["lifecycle_features"][feature] = False
    lifecycle(f"unsupported-{feature}", steps, code, manifest=manifest)


def rpc(direction, message):
    return {"direction": direction, "message": message}


init_rpc = rpc(
    "runner", {"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": INITIALIZE}
)
init_reply = rpc(
    "provider",
    {"jsonrpc": "2.0", "id": "init", "result": {"contract_version": "0.1", "manifest": MANIFEST}},
)
invoke_rpc = rpc(
    "runner", {"jsonrpc": "2.0", "id": "rpc-1", "method": "invoke", "params": INVOCATION}
)
event_rpc = rpc("provider", {"jsonrpc": "2.0", "method": "event", "params": EVENT})
outcome_rpc = rpc("provider", {"jsonrpc": "2.0", "id": "rpc-1", "result": OUTCOME})
add(
    "stdio-session",
    "stdio-session",
    [init_rpc, init_reply, invoke_rpc, event_rpc, outcome_rpc],
    spec="transports.md",
)
add("rpc-before-initialize", "stdio-session", [invoke_rpc], "PROTOCOL_VIOLATION", "transports.md")
add(
    "rpc-wrong-correlation",
    "stdio-session",
    [
        init_rpc,
        init_reply,
        invoke_rpc,
        rpc("provider", {"jsonrpc": "2.0", "id": "wrong", "result": OUTCOME}),
    ],
    "PROTOCOL_VIOLATION",
    "transports.md",
)
add(
    "rpc-duplicate-response",
    "stdio-session",
    [init_rpc, init_reply, invoke_rpc, outcome_rpc, outcome_rpc],
    "PROTOCOL_VIOLATION",
    "transports.md",
)
add(
    "rpc-event-after-terminal",
    "stdio-session",
    [init_rpc, init_reply, invoke_rpc, outcome_rpc, event_rpc],
    "PROTOCOL_VIOLATION",
    "transports.md",
)
add(
    "rpc-duplicate-initialize",
    "stdio-session",
    [init_rpc, init_reply, init_rpc],
    "PROTOCOL_VIOLATION",
    "transports.md",
)
add(
    "rpc-invalid-selection",
    "stdio-session",
    [
        init_rpc,
        rpc(
            "provider",
            {
                "jsonrpc": "2.0",
                "id": "init",
                "result": {"contract_version": "0.2", "manifest": MANIFEST},
            },
        ),
    ],
    "CONTRACT_VERSION_UNSUPPORTED",
    "transports.md",
)

# Hex bytes permit language-neutral framing tests without JSON string decoding ambiguity.
body = json.dumps(
    {"jsonrpc": "2.0", "method": "event", "params": {**EVENT, "payload": "é"}},
    ensure_ascii=False,
    separators=(",", ":"),
).encode("utf-8")
frame = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
add(
    "utf8-framing",
    "framing",
    {"chunks": [frame[:8].hex(), frame[8:31].hex(), frame[31:].hex()], "message_count": 1},
    spec="transports.md",
)
add(
    "coalesced-framing",
    "framing",
    {"chunks": [(frame + frame).hex()], "message_count": 2},
    spec="transports.md",
)
for identity, data in (
    ("duplicate-length", b"Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}"),
    ("newline-framing", b"Content-Length: 2\n\n{}"),
    ("truncated-framing", frame[:-1]),
    ("zero-length", b"Content-Length: 0\r\n\r\n"),
):
    add(
        identity,
        "framing",
        {"chunks": [data.hex()], "message_count": 1},
        "PROTOCOL_VIOLATION",
        "transports.md",
    )

add(
    "dangling-schema-reference",
    "capability",
    {**CAPABILITY, "input_schema": {"$ref": "#/missing"}},
    "INVALID_PROVIDER_OUTPUT",
)
add(
    "nested-schema-id",
    "capability",
    {
        **CAPABILITY,
        "input_schema": {"$defs": {"inner": {"$id": "urn:example:inner", "type": "string"}}},
    },
    "INVALID_PROVIDER_OUTPUT",
)
lifecycle(
    "fractional-deadline-completion",
    [
        step("accept", {**INVOCATION, "deadline": "2026-10-13T00:00:00.0000001Z"}, BEFORE),
        step("outcome", OUTCOME, "2026-10-13T00:00:00.00000001Z"),
    ],
)
lifecycle(
    "fractional-deadline-expiry",
    [
        step("accept", {**INVOCATION, "deadline": "2026-10-13T00:00:00.0000001Z"}, BEFORE),
        step(
            "outcome",
            {"invocation_id": "attempt-1", "state": "DEADLINE_EXCEEDED"},
            "2026-10-13T00:00:00.0000001Z",
        ),
    ],
)
add(
    "leap-second-unsupported",
    "invocation",
    {**INVOCATION, "deadline": "2026-12-31T23:59:60Z"},
    "INVALID_INVOCATION",
)
add(
    "estimated-budget",
    "invocation",
    {**INVOCATION, "resource_budget": {"x": {"kind": "ESTIMATED", "unit": "u", "value": 1}}},
    "INVALID_INVOCATION",
)
add(
    "budget-without-vcp",
    "invocation",
    {**{k: v for k, v in INVOCATION.items() if k != "vcp_version"}, "resource_budget": USAGE},
    "INVALID_INVOCATION",
)
add(
    "invalid-extension-namespace",
    "provider-manifest",
    {**MANIFEST, "extensions": {"example": True}},
    "INVALID_PROVIDER_OUTPUT",
)
numeric_manifest = deepcopy(MANIFEST)
numeric_manifest["capabilities"][0].update(
    input_schema={"const": 1}, config_schema={"const": 0}, output_schema={"const": 1}
)
numeric_invocation = {**INVOCATION, "input": 1, "config": 0}
lifecycle(
    "boolean-input-const",
    [step("accept", {**numeric_invocation, "input": True})],
    "INVALID_INPUT",
    manifest=numeric_manifest,
)
lifecycle(
    "boolean-config-const",
    [step("accept", {**numeric_invocation, "config": False})],
    "INVALID_CONFIG",
    manifest=numeric_manifest,
)
lifecycle(
    "boolean-output-const",
    [step("accept", numeric_invocation), step("outcome", {**OUTCOME, "output": True})],
    "INVALID_PROVIDER_OUTPUT",
    manifest=numeric_manifest,
)
lifecycle(
    "numeric-const-completed",
    [step("accept", numeric_invocation), step("outcome", {**OUTCOME, "output": 1})],
    manifest=numeric_manifest,
)
bool_manifest = deepcopy(MANIFEST)
bool_manifest["capabilities"][0]["input_schema"] = {"type": "array", "uniqueItems": True}
lifecycle(
    "bool-number-unique-items",
    [step("accept", {**INVOCATION, "input": [True, 1]}), outcome],
    manifest=bool_manifest,
)
lifecycle(
    "duplicate-number-items",
    [step("accept", {**INVOCATION, "input": [1, 1.0]})],
    "INVALID_INPUT",
    manifest=bool_manifest,
)
add(
    "rpc-two-correlation-mismatch",
    "stdio-session",
    [
        init_rpc,
        init_reply,
        invoke_rpc,
        rpc(
            "provider",
            {"jsonrpc": "2.0", "id": "rpc-1", "result": {**OUTCOME, "invocation_id": "wrong"}},
        ),
    ],
    "PROTOCOL_VIOLATION",
    "transports.md",
)
add(
    "rpc-error-after-event",
    "stdio-session",
    [
        init_rpc,
        init_reply,
        invoke_rpc,
        event_rpc,
        rpc(
            "provider",
            {
                "jsonrpc": "2.0",
                "id": "rpc-1",
                "error": {
                    "code": -32000,
                    "message": "failed",
                    "data": {"code": "com.example.failed", "message": "failed"},
                },
            },
        ),
    ],
    "PROTOCOL_VIOLATION",
    "transports.md",
)
add(
    "rpc-cancel-completion-race",
    "stdio-session",
    [
        init_rpc,
        init_reply,
        invoke_rpc,
        rpc("runner", {"jsonrpc": "2.0", "id": "cancel-1", "method": "cancel", "params": CANCEL}),
        outcome_rpc,
        rpc("provider", {"jsonrpc": "2.0", "id": "cancel-1", "result": None}),
    ],
    spec="transports.md",
)

(ROOT / "manifest.json").write_text(
    json.dumps({"contract_version": "0.1", "status": "DRAFT", "cases": cases}, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Provider Contract conformance: {len(cases)} cases")
