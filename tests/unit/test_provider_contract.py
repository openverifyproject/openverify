from copy import deepcopy
from typing import cast

import pytest
from pydantic import JsonValue

from openverify.provider import (
    LifecycleValidator,
    ProviderContractError,
    ProviderEvent,
    parse_invocation,
    parse_outcome,
    parse_provider_manifest,
    parse_provider_object,
    validate_invocation,
    validate_outcome,
    validate_provider_event,
    validate_provider_manifest,
)
from openverify.provider.stdio import FrameDecoder, StdioSessionValidator, encode_frame
from openverify.provider.validation import timestamp


def manifest_data() -> dict[str, JsonValue]:
    return {
        "provider_id": "com.example.provider.echo",
        "provider_version": "1",
        "supported_contract_versions": ["0.1"],
        "supported_vcp_versions": ["draft"],
        "capabilities": [
            {
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
        ],
    }


def invocation_data() -> dict[str, JsonValue]:
    return {
        "invocation_id": "attempt-1",
        "contract_version": "0.1",
        "capability_id": "com.example.execution.echo",
        "capability_version": "1",
        "input": "hello",
        "config": {},
    }


def outcome_data() -> dict[str, JsonValue]:
    return {"invocation_id": "attempt-1", "state": "COMPLETED", "output": "hello"}


def running() -> LifecycleValidator:
    validator = LifecycleValidator(parse_provider_manifest(manifest_data()))
    validator.initialize(
        {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]}
    )
    validator.accept(invocation_data())
    return validator


@pytest.mark.parametrize(
    "raw", ['{"invocation_id":"a","invocation_id":"b"}', "{", "NaN", "Infinity", b"\xff"]
)
def test_provider_json_rejections(raw: str | bytes) -> None:
    with pytest.raises(ProviderContractError, match="INVALID_INVOCATION"):
        parse_invocation(raw)


@pytest.mark.parametrize("raw", [float("nan"), float("inf"), {"config": (1, 2)}, {1: "x"}])
def test_provider_nonjson_rejections(raw: object) -> None:
    with pytest.raises(ProviderContractError, match="INVALID_INVOCATION"):
        parse_invocation(cast(JsonValue, raw))


def test_typed_validation_and_mutation_boundaries() -> None:
    manifest = parse_provider_manifest(manifest_data())
    validate_provider_manifest(manifest)
    invocation = parse_invocation(invocation_data())
    validate_invocation(invocation)
    validate_outcome(parse_outcome(outcome_data()))
    event = cast(
        "ProviderEvent",
        parse_provider_object(
            "provider-event",
            {"invocation_id": "attempt-1", "sequence": 1, "kind": "progress", "payload": None},
        ),
    )
    validate_provider_event(event)
    validator = LifecycleValidator(manifest)
    manifest.capabilities.clear()
    validator.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})
    validator.accept(invocation_data())  # Validator retained its own snapshot.


def test_rejected_ids_cannot_be_retried() -> None:
    validator = running()
    with pytest.raises(ProviderContractError, match="INVALID_INPUT"):
        validator.accept({**invocation_data(), "invocation_id": "bad", "input": 1})
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.accept({**invocation_data(), "invocation_id": "bad"})


def test_work_before_init_and_second_init() -> None:
    validator = LifecycleValidator(parse_provider_manifest(manifest_data()))
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.accept(invocation_data())
    request: JsonValue = {"supported_contract_versions": ["0.1"], "supported_vcp_versions": []}
    validator.initialize(request)
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.initialize(request)


def test_initialization_failure_closes_lifecycle() -> None:
    validator = LifecycleValidator(parse_provider_manifest(manifest_data()))
    with pytest.raises(ProviderContractError, match="CONTRACT_VERSION_UNSUPPORTED"):
        validator.initialize({"supported_contract_versions": ["0.2"], "supported_vcp_versions": []})
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})


def test_fractional_deadline_precision_and_clock_adjustment() -> None:
    assert timestamp("2026-10-13T00:00:00.0000001Z") > timestamp("2026-10-13T00:00:00Z")
    validator = running()
    validator.accept(
        {
            **invocation_data(),
            "invocation_id": "precise",
            "deadline": "2026-10-13T00:00:00.0000001Z",
        },
        now="2026-10-13T00:00:00Z",
    )
    validator.outcome(
        {**outcome_data(), "invocation_id": "precise"}, now="2026-10-13T00:00:00.00000001Z"
    )
    validator.accept(
        {**invocation_data(), "invocation_id": "expired", "deadline": "2026-10-13T00:00:00Z"},
        now="2026-10-13T00:00:01Z",
    )
    validator.outcome(
        {"invocation_id": "expired", "state": "DEADLINE_EXCEEDED"}, now="2026-10-12T23:59:59Z"
    )


def test_local_pointer_schemas_and_annotation_data() -> None:
    raw = manifest_data()
    capability = cast(list[dict[str, JsonValue]], raw["capabilities"])[0]
    capability["input_schema"] = {
        "$defs": {"text": {"type": "string"}},
        "$ref": "#/$defs/text",
        "default": {"$ref": "annotation-only"},
    }
    validator = LifecycleValidator(parse_provider_manifest(raw))
    validator.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})
    validator.accept(invocation_data())


def test_deadline_requires_clock_and_expired_invocation_has_no_events() -> None:
    validator = running()
    data: JsonValue = {
        **invocation_data(),
        "invocation_id": "expired",
        "deadline": "2026-10-13T00:00:00Z",
    }
    validator.accept(data, now="2026-10-13T00:00:01Z")
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.event(
            {"invocation_id": "expired", "sequence": 1, "kind": "progress", "payload": None}
        )
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.outcome({"invocation_id": "expired", "state": "DEADLINE_EXCEEDED"})
    validator.outcome(
        {"invocation_id": "expired", "state": "DEADLINE_EXCEEDED"}, now="2026-10-13T00:00:01Z"
    )


def test_stdio_utf8_split_at_every_byte_and_coalescing() -> None:
    message: JsonValue = {"jsonrpc": "2.0", "id": "é", "result": "你好"}
    frame = encode_frame(message)
    for split in range(len(frame) + 1):
        decoder = FrameDecoder()
        assert decoder.feed(frame[:split]) + decoder.feed(frame[split:]) == [message]
        decoder.finish()
    decoder = FrameDecoder()
    assert decoder.feed(frame + frame) == [message, message]


@pytest.mark.parametrize(
    "frame",
    [
        b"Content-Length: -1\r\n\r\n",
        b"Content-Length: 100000000000000000000000000000\r\n\r\n",
        b"Content-Length: 0\r\n\r\n",
        b"Content-Length: 2\r\nContent-Type: application/json\r\n\r\n{}",
        b"Content-Length: 2\r\n\r\n\xff\xff",
    ],
)
def test_stdio_invalid_frames_poison_decoder(frame: bytes) -> None:
    decoder = FrameDecoder()
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        decoder.feed(frame)
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        decoder.feed(b"")


def session() -> StdioSessionValidator:
    validator = StdioSessionValidator()
    validator.runner_message(
        {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {"supported_contract_versions": ["0.1"], "supported_vcp_versions": []},
        }
    )
    validator.provider_message(
        {
            "jsonrpc": "2.0",
            "id": "init",
            "result": {"contract_version": "0.1", "manifest": manifest_data()},
        }
    )
    return validator


def test_stdio_cancel_race_and_two_correlations() -> None:
    validator = session()
    validator.runner_message(
        {"jsonrpc": "2.0", "id": "invoke", "method": "invoke", "params": invocation_data()}
    )
    validator.runner_message(
        {
            "jsonrpc": "2.0",
            "id": "cancel",
            "method": "cancel",
            "params": {"invocation_id": "attempt-1"},
        }
    )
    validator.provider_message({"jsonrpc": "2.0", "id": "invoke", "result": outcome_data()})
    validator.provider_message({"jsonrpc": "2.0", "id": "cancel", "result": None})
    validator.finish()
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.provider_message({"jsonrpc": "2.0", "id": "invoke", "result": outcome_data()})


def test_stdio_rejection_before_work_vs_error_after_events() -> None:
    validator = session()
    validator.runner_message(
        {
            "jsonrpc": "2.0",
            "id": "bad",
            "method": "invoke",
            "params": {**invocation_data(), "input": 1},
        }
    )
    validator.provider_message(
        {
            "jsonrpc": "2.0",
            "id": "bad",
            "error": {
                "code": -32000,
                "message": "bad input",
                "data": {"code": "INVALID_INPUT", "message": "bad input"},
            },
        }
    )
    validator.finish()
    validator = session()
    validator.runner_message(
        {"jsonrpc": "2.0", "id": "work", "method": "invoke", "params": invocation_data()}
    )
    validator.provider_message(
        {
            "jsonrpc": "2.0",
            "method": "event",
            "params": {
                "invocation_id": "attempt-1",
                "sequence": 1,
                "kind": "progress",
                "payload": None,
            },
        }
    )
    with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
        validator.provider_message(
            {
                "jsonrpc": "2.0",
                "id": "work",
                "error": {
                    "code": -32000,
                    "message": "failed",
                    "data": {"code": "com.example.failed", "message": "failed"},
                },
            }
        )


def test_lifecycle_bad_output_does_not_consume_terminal_slot() -> None:
    validator = running()
    with pytest.raises(ProviderContractError, match="INVALID_PROVIDER_OUTPUT"):
        validator.outcome({**outcome_data(), "output": 1})
    validator.outcome(outcome_data())
    validator.finish()


def test_invocation_nested_data_is_snapshotted() -> None:
    raw = invocation_data()
    raw["context"] = {"key": []}
    validator = running()
    other = deepcopy(raw)
    other["invocation_id"] = "attempt-2"
    validator.accept(other)
    other["input"] = 2
    validator.outcome({**outcome_data(), "invocation_id": "attempt-2"})
