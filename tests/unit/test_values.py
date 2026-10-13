import itertools
from typing import cast

import pytest
from pydantic import JsonValue, ValidationError

from openverify import (
    ProtocolError,
    fingerprint,
    flattened_status,
    inspect_definition,
    parse_result,
    serialize,
    validate_result,
)
from openverify.model import Result
from openverify.serialization import decode, to_data
from openverify.validation import parse_object
from tests.helpers import definition


@pytest.mark.parametrize(
    "disposition,outcome,applicability,determination",
    list(
        itertools.product(
            ["EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED"],
            [None, "SUCCESS", "ERROR"],
            [None, "APPLICABLE", "NOT_APPLICABLE"],
            [None, "KNOWN", "UNKNOWN"],
        )
    ),
)
def test_state_space(
    disposition: str, outcome: str | None, applicability: str | None, determination: str | None
) -> None:
    valid = (
        disposition != "EXECUTED"
        and outcome is None
        and applicability is None
        and determination is None
        or disposition == "EXECUTED"
        and outcome == "ERROR"
        and applicability is None
        and determination is None
        or disposition == "EXECUTED"
        and outcome == "SUCCESS"
        and (
            applicability == "NOT_APPLICABLE"
            and determination is None
            or applicability == "APPLICABLE"
            and determination in ("KNOWN", "UNKNOWN")
        )
    )
    data: dict[str, JsonValue] = {
        "protocol": "draft",
        "disposition": disposition,
        "execution_outcome": outcome,
        "applicability": applicability,
        "determination": determination,
    }
    if valid:
        result = parse_result(data)
        assert parse_result(serialize(result)) == result
    else:
        with pytest.raises(ProtocolError, match="RESULT_STATE"):
            parse_result(data)


@pytest.mark.parametrize("score", [-0.1, 1.1, True, "0.5"])
def test_strict_scores(score: JsonValue) -> None:
    with pytest.raises(ProtocolError, match="PROTOCOL_STRUCTURE"):
        parse_result(
            {
                "protocol": "draft",
                "disposition": "EXECUTED",
                "execution_outcome": "SUCCESS",
                "applicability": "APPLICABLE",
                "determination": "KNOWN",
                "score": score,
            }
        )


@pytest.mark.parametrize(
    "payload",
    ['{"protocol":"draft","protocol":"draft"}', '{"score":NaN}', '{"score":Infinity}', "{"],
)
def test_json_rejections(payload: str) -> None:
    with pytest.raises(ProtocolError, match="PROTOCOL_JSON"):
        decode(payload)


@pytest.mark.parametrize("payload", [float("nan"), float("inf"), {"x": (1, 2)}, {1: "x"}])
def test_non_json_values(payload: object) -> None:
    with pytest.raises(ProtocolError, match="PROTOCOL_JSON"):
        decode(cast(JsonValue, payload))


def test_partial_flattening_and_error_contract() -> None:
    assert flattened_status(Result(disposition="SKIPPED")) == "SKIP"
    assert flattened_status(Result(disposition="EXECUTED", execution_outcome="ERROR")) == "ERROR"
    for disposition in ("DEFERRED", "CANCELLED"):
        with pytest.raises(ProtocolError, match="RESULT_PROJECTION"):
            flattened_status(parse_result({"protocol": "draft", "disposition": disposition}))
    error = ProtocolError("RESULT_STATE", "bad", "/verdict")
    assert error.as_dict()["path"] == "/verdict"


def test_required_null_and_optional_extensions_roundtrip() -> None:
    artifact = parse_object(
        "artifact-ref",
        {
            "id": "a",
            "type": "application/json",
            "locator": None,
            "extensions": [
                {"namespace": "org.example:data", "version": "1", "required": False, "data": None}
            ],
        },
    )
    assert parse_object("artifact-ref", serialize(artifact)) == artifact
    assert '"data":null' in serialize(artifact)
    assert '"locator":null' in serialize(artifact)


def test_frozen_outer_model_and_revalidation() -> None:
    result = Result(disposition="SKIPPED")
    with pytest.raises(ValidationError):
        result.disposition = "EXECUTED"
    bad = result.model_copy(update={"verdict": "PASS"})
    with pytest.raises(ProtocolError, match="RESULT_STATE"):
        validate_result(bad)


def test_fingerprint_and_inspection() -> None:
    d = definition()
    assert fingerprint(d) == fingerprint(d.model_copy(deep=True))
    assert fingerprint(d) != fingerprint(d.model_copy(update={"version": "2"}))
    assert fingerprint(d).startswith("local-sha256:")
    assert inspect_definition(d)["subject"] == "article-1"
    assert to_data(d) is not None


@pytest.mark.parametrize(
    "value",
    [
        {"unit": "s", "kind": "EXACT"},
        {"unit": "s", "kind": "EXACT", "value": 1, "minimum": 0},
        {"unit": "s", "kind": "RANGE", "minimum": 2, "maximum": 1},
        {"unit": "s", "kind": "UNKNOWN", "value": 0},
    ],
)
def test_resource_invariants(value: dict[str, JsonValue]) -> None:
    with pytest.raises(ProtocolError, match="RESOURCE_MEASUREMENT"):
        parse_object("resource", value)


def test_metadata_cannot_override_core() -> None:
    result = parse_result(
        {"protocol": "draft", "disposition": "SKIPPED", "metadata": {"verdict": "PASS"}}
    )
    assert result.verdict is None
    with pytest.raises(ProtocolError, match="PROTOCOL_STRUCTURE"):
        parse_result({**cast(dict[str, JsonValue], to_data(result)), "surprise": True})


def test_json_escapes_are_preserved_in_utf8_transport() -> None:
    result = parse_result({"protocol": "draft", "disposition": "SKIPPED", "output": "\ud800"})
    encoded = serialize(result).encode("utf-8")
    assert parse_result(encoded) == result
