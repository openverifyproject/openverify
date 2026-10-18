from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import JsonValue

from openverify.provider import (
    LifecycleValidator,
    ProviderContractError,
    parse_provider_manifest,
    serialize,
    wire_data,
)
from openverify.serialization import json_equal
from tests.property.test_invariants import json_values
from tests.unit.test_provider_contract import invocation_data, manifest_data, outcome_data, running


@given(json_values)
def test_provider_extension_roundtrip(value: JsonValue) -> None:
    raw: dict[str, JsonValue] = {**manifest_data(), "extensions": {"com.example.future": value}}
    parsed = parse_provider_manifest(raw)
    assert json_equal(raw, wire_data(parse_provider_manifest(serialize(parsed))))


@given(st.lists(st.integers(1, 100), max_size=20))
def test_provider_event_monotonicity(sequences: list[int]) -> None:
    validator = running()
    previous = 0
    for sequence in sequences:
        event: JsonValue = {
            "invocation_id": "attempt-1",
            "sequence": sequence,
            "kind": "progress",
            "payload": None,
        }
        if (previous == 0 and sequence != 1) or sequence <= previous:
            with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
                validator.event(event)
            break
        validator.event(event)
        previous = sequence
    validator.outcome(outcome_data())
    validator.finish()


@given(st.text(min_size=1, max_size=50), st.sampled_from(["event", "outcome"]))
def test_provider_correlation(identity: str, operation: str) -> None:
    validator = running()
    data: JsonValue = (
        {"invocation_id": identity, "sequence": 1, "kind": "progress", "payload": None}
        if operation == "event"
        else {**outcome_data(), "invocation_id": identity}
    )
    action = validator.event if operation == "event" else validator.outcome
    if identity == "attempt-1":
        action(data)
    else:
        with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
            action(data)


@given(st.lists(st.text(min_size=1, max_size=20), unique=True, max_size=5), json_values)
def test_provider_manifest_roundtrip(versions: list[str], annotation: JsonValue) -> None:
    raw = manifest_data()
    raw["supported_vcp_versions"] = cast(list[JsonValue], versions)
    raw["extensions"] = {"com.example.manifest": annotation}
    parsed = parse_provider_manifest(raw)
    assert json_equal(raw, wire_data(parse_provider_manifest(serialize(parsed))))


@given(st.booleans())
def test_provider_bool_number_distinction(flag: bool) -> None:
    # Exercise schema equality through enum, not just Python's equality operator.
    raw = manifest_data()
    capabilities = cast(list[dict[str, JsonValue]], raw["capabilities"])
    capabilities[0]["input_schema"] = {"enum": [int(flag)]}
    validator = LifecycleValidator(parse_provider_manifest(raw))
    validator.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})
    with pytest.raises(ProviderContractError, match="INVALID_INPUT"):
        validator.accept({**invocation_data(), "input": flag})
    validator.accept({**invocation_data(), "invocation_id": "attempt-2", "input": int(flag)})


@given(st.integers(0, 5))
def test_provider_exactly_one_terminal(count: int) -> None:
    validator = running()
    if count == 0:
        with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
            validator.finish()
        return
    validator.outcome(outcome_data())
    for _ in range(count - 1):
        with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
            validator.outcome(outcome_data())
    validator.finish()
