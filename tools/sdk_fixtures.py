"""Author shared, prose-derived cases. Does not use an SDK as an oracle."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = []


def case(contract, name, target, value, error=None, **extra):
    item = {
        "id": f"{contract}.{name}",
        "contract": contract,
        "version": "draft" if contract == "vcp" else "0.1",
        "type": target,
        "operation": "parse",
        "input": value,
        "expected": {"accepted": error is None},
        "features": ["standalone", target],
        **extra,
    }
    if error:
        item["expected"]["error"] = error
    else:
        item["expected"]["normalized"] = value
    CASES.append(item)


def main():
    base = {
        "protocol": "draft",
        "disposition": "EXECUTED",
        "execution_outcome": "SUCCESS",
        "applicability": "APPLICABLE",
        "determination": "KNOWN",
        "verdict": "PASS",
    }
    case("vcp", "known", "result", base)
    for key in ("protocol", "disposition"):
        value = dict(base)
        del value[key]
        case("vcp", "missing-" + key, "result", value, "PROTOCOL_STRUCTURE")
    for name, patch, error in [
        ("version", {"protocol": "1.0"}, "PROTOCOL_VERSION"),
        ("score-bool", {"score": True}, "PROTOCOL_STRUCTURE"),
        ("score-negative", {"score": -0.1}, "PROTOCOL_STRUCTURE"),
        ("score-high", {"score": 1.1}, "PROTOCOL_STRUCTURE"),
        ("score-string", {"score": "1"}, "PROTOCOL_STRUCTURE"),
        ("unknown-core", {"surprise": 1}, "PROTOCOL_STRUCTURE"),
        ("bad-enum", {"verdict": "MAYBE"}, "PROTOCOL_STRUCTURE"),
        (
            "unknown-judgment",
            {"determination": "UNKNOWN", "verdict": None, "judgment": None},
            "RESULT_STATE",
        ),
        ("unknown-verdict", {"determination": "UNKNOWN"}, "RESULT_STATE"),
        ("error-verdict", {"execution_outcome": "ERROR"}, "RESULT_STATE"),
        ("null-judgment", {"judgment": None}, None),
        ("payload", {"output": {"protocol": "other", "extensions": [{"required": True}]}}, None),
        ("optional-null", {"score": None}, None),
        ("severity", {"severity": {"domain": "custom", "label": "x"}}, None),
    ]:
        case("vcp", name, "result", {**base, **patch}, error)
    for state in ("SKIPPED", "DEFERRED", "CANCELLED"):
        value = {"protocol": "draft", "disposition": state}
        case("vcp", state.lower(), "result", value)
        case(
            "vcp", state.lower() + "-observations", "result", {**value, "score": 0}, "RESULT_STATE"
        )
    for outcome in ("SUCCESS", "ERROR"):
        case(
            "vcp",
            outcome.lower() + "-missing-axis",
            "result",
            {"protocol": "draft", "disposition": "EXECUTED", "execution_outcome": outcome},
            "RESULT_STATE" if outcome == "SUCCESS" else None,
        )
    case(
        "vcp",
        "missing-execution",
        "result",
        {"protocol": "draft", "disposition": "EXECUTED"},
        "RESULT_STATE",
    )
    for kind in ("CONTINUE", "STOP_SUCCESS", "STOP_FAILURE", "RETRY", "DEFER", "ROUTE"):
        value = {"protocol": "draft", "kind": kind}
        if kind == "ROUTE":
            value["destination"] = "review"
        case("vcp", "decision-" + kind.lower(), "decision", value)
    # No cross-language Decision diagnostic is specified by prose; assert rejection only.
    case("vcp", "route-missing", "decision", {"protocol": "draft", "kind": "ROUTE"}, "*")
    case(
        "vcp",
        "continue-destination",
        "decision",
        {"protocol": "draft", "kind": "CONTINUE", "destination": "x"},
        "*",
    )
    for value in (
        {"message": "why"},
        {"structured_data": {}},
        {"locator": []},
        {"structured_data": False},
    ):
        case("vcp", "evidence-" + str(len(CASES)), "evidence", value)
    case("vcp", "empty-evidence", "evidence", {}, "EVIDENCE_EMPTY")
    case("vcp", "null-evidence", "evidence", {"structured_data": None}, "EVIDENCE_EMPTY")
    case("vcp", "id-only-evidence", "evidence", {"id": "e"}, "EVIDENCE_EMPTY")
    for kind in ("EXACT", "ESTIMATED", "UNKNOWN", "RANGE"):
        value = {"unit": "seconds", "kind": kind}
        if kind in ("EXACT", "ESTIMATED"):
            value["value"] = 0
        if kind == "RANGE":
            value.update(minimum=0, maximum=2)
        case("vcp", "resource-" + kind.lower(), "resource", value)
    case(
        "vcp",
        "range-reversed",
        "resource",
        {"unit": "x", "kind": "RANGE", "minimum": 3, "maximum": 2},
        "RESOURCE_MEASUREMENT",
    )
    case("vcp", "exact-missing", "resource", {"unit": "x", "kind": "EXACT"}, "RESOURCE_MEASUREMENT")
    case(
        "vcp",
        "unknown-value",
        "resource",
        {"unit": "x", "kind": "UNKNOWN", "value": 0},
        "RESOURCE_MEASUREMENT",
    )
    for required in (False, True):
        case(
            "vcp",
            "extension-" + str(required).lower(),
            "extension",
            {
                "namespace": "com.example:extra",
                "version": "1",
                "required": required,
                "data": {"x": None},
            },
            "EXTENSION_UNSUPPORTED" if required else None,
        )
    case("vcp", "nested-empty-evidence", "result", {**base, "evidence": [{}]}, "EVIDENCE_EMPTY")
    case(
        "vcp",
        "nested-required-extension",
        "result",
        {
            **base,
            "extensions": [
                {"namespace": "com.example:extra", "version": "1", "required": True, "data": {}}
            ],
        },
        "EXTENSION_UNSUPPORTED",
    )
    manifest = {
        "provider_id": "com.example.provider",
        "provider_version": "1",
        "supported_contract_versions": ["0.1"],
        "supported_vcp_versions": [],
        "capabilities": [],
    }
    capability = {
        "capability_id": "com.example.echo",
        "capability_version": "1",
        "input_schema": {"type": "string"},
        "config_schema": True,
        "output_schema": True,
        "lifecycle_features": dict.fromkeys(
            ["streaming", "cancellation", "deadlines", "resource_reporting"], False
        ),
    }
    case("provider", "minimal-manifest", "provider-manifest", manifest)
    case("provider", "capability", "capability", capability)
    case(
        "provider",
        "manifest-capability",
        "provider-manifest",
        {**manifest, "capabilities": [capability]},
    )
    case(
        "provider",
        "duplicate-capability",
        "provider-manifest",
        {**manifest, "capabilities": [capability, capability]},
        "INVALID_PROVIDER_OUTPUT",
    )
    case(
        "provider",
        "unadvertised-vcp",
        "provider-manifest",
        {**manifest, "capabilities": [{**capability, "vcp_version": "draft"}]},
        "INVALID_PROVIDER_OUTPUT",
    )
    for name, patch in [
        ("bad-id", {"provider_id": "echo"}),
        ("unknown-core", {"extra": 1}),
        ("optional-null", {"extensions": None}),
        ("duplicate-versions", {"supported_contract_versions": ["0.1", "0.1"]}),
    ]:
        case(
            "provider", name, "provider-manifest", {**manifest, **patch}, "INVALID_PROVIDER_OUTPUT"
        )
    for state in ("COMPLETED", "ERROR", "CANCELLED", "DEADLINE_EXCEEDED"):
        value = {"invocation_id": "i", "state": state}
        if state == "COMPLETED":
            value["output"] = None
        if state == "ERROR":
            value["error"] = {"code": "com.example.failed", "message": "failed"}
        case("provider", "outcome-" + state.lower(), "outcome", value)
    for name, value in [
        ("completed-missing", {"state": "COMPLETED"}),
        ("cancelled-output", {"state": "CANCELLED", "output": None}),
        ("error-missing", {"state": "ERROR"}),
        ("fake-fail", {"state": "FAIL"}),
        ("verdict", {"state": "COMPLETED", "output": None, "verdict": "PASS"}),
    ]:
        case(
            "provider", name, "outcome", {"invocation_id": "i", **value}, "INVALID_PROVIDER_OUTPUT"
        )
    case(
        "provider",
        "optional-extension",
        "outcome",
        {
            "invocation_id": "i",
            "state": "COMPLETED",
            "output": None,
            "extensions": {"com.example.annotation": {"required": True, "x": None}},
        },
    )
    invocation = {
        "invocation_id": "i",
        "contract_version": "0.1",
        "capability_id": "com.example.echo",
        "capability_version": "1",
        "input": None,
        "config": None,
    }
    case("provider", "invocation", "invocation", invocation)
    case(
        "provider",
        "contract-version",
        "invocation",
        {**invocation, "contract_version": "2"},
        "CONTRACT_VERSION_UNSUPPORTED",
    )
    case(
        "provider",
        "vcp-version",
        "invocation",
        {**invocation, "vcp_version": "1"},
        "INVALID_INVOCATION",
    )
    for name, schema in [
        ("external-ref", {"$ref": "https://example.com/untrusted"}),
        ("dangling-ref", {"$ref": "#/$defs/missing"}),
        ("annotation-ref", {"default": {}, "$ref": "#/default"}),
        ("nested-id", {"$defs": {"x": {"$id": "urn:other", "type": "string"}}}),
        ("wrong-draft", {"$schema": "http://json-schema.org/draft-07/schema#"}),
        ("invalid-type", {"type": 42}),
    ]:
        case(
            "provider",
            "schema-reject-" + name,
            "data",
            None,
            "INVALID_PROVIDER_OUTPUT",
            operation="data",
            schema=schema,
        )
    for name, payload, accepted in [
        ("message", {"message": "checked"}, True),
        ("empty", {}, False),
    ]:
        case(
            "provider",
            "event-evidence-" + name,
            "provider-event",
            {"invocation_id": "i", "sequence": 1, "kind": "evidence", "payload": payload},
            None if accepted else "INVALID_PROVIDER_OUTPUT",
        )
    case(
        "provider",
        "event-resource-range",
        "provider-event",
        {
            "invocation_id": "i",
            "sequence": 1,
            "kind": "resource_usage",
            "payload": {"time": {"unit": "s", "kind": "RANGE", "minimum": 2, "maximum": 1}},
        },
        "INVALID_PROVIDER_OUTPUT",
    )
    case(
        "provider",
        "event-sequence-bool",
        "provider-event",
        {"invocation_id": "i", "sequence": True, "kind": "progress", "payload": None},
        "INVALID_PROVIDER_OUTPUT",
    )
    case(
        "provider",
        "schema-default-is-annotation",
        "data",
        {},
        operation="data",
        schema={"properties": {"x": {"default": 1}}},
    )
    # Draft 2020-12 features, reference resolution, JSON type equality and annotation formats.
    for name, schema, value, accepted in [
        ("boolean-true", True, None, True),
        ("boolean-false", False, None, False),
        ("bool-number-const", {"const": 1}, True, False),
        ("numeric-const", {"const": 1}, 1.0, True),
        ("unique", {"uniqueItems": True}, [1, True], True),
        ("unique-number", {"uniqueItems": True}, [1, 1.0], False),
        ("local-ref", {"$defs": {"n": {"type": "integer"}}, "$ref": "#/$defs/n"}, 1, True),
        (
            "local-ref-reject",
            {"$defs": {"n": {"type": "integer"}}, "$ref": "#/$defs/n"},
            "1",
            False,
        ),
        (
            "conditional",
            {"if": {"type": "number"}, "then": {"minimum": 2}, "else": {"type": "null"}},
            1,
            False,
        ),
        ("prefix-items", {"prefixItems": [{"type": "string"}], "items": False}, ["x", 1], False),
        (
            "unevaluated",
            {"allOf": [{"properties": {"x": True}}], "unevaluatedProperties": False},
            {"x": 1},
            True,
        ),
        ("format-annotation", {"format": "date-time"}, "not-a-date", True),
    ]:
        case(
            "provider",
            "schema-" + name,
            "data",
            value,
            None if accepted else "INVALID_INPUT",
            operation="data",
            schema=schema,
        )
    root = ROOT / "conformance/sdk"
    manifest_out = {
        "format": 1,
        "status": "DRAFT",
        "spec_revision": "5f17f402a270882f244a54dde25eda92a085eb39",
        "cases": [],
    }
    for item in CASES:
        relative = f"{item['contract']}/{item['id']}.json"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest_out["cases"].append(relative)
    (root / "manifest.json").write_text(
        json.dumps(manifest_out, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
