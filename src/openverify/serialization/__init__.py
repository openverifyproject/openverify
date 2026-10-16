"""Strict JSON interchange, without claiming canonical cross-language bytes."""

import json
from enum import StrEnum
from typing import cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.model import InputResolution, Result, Value


def json_equal(left: JsonValue, right: JsonValue) -> bool:
    """Compare parsed JSON snapshots; bool is distinct from the JSON number type.

    Numeric comparison uses existing parsed values, not canonical hashing or a
    new cross-engine precision/rounding rule. Callers supply validated JSON.
    """
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            json_equal(value, right[key]) for key, value in left.items()
        )
    return left == right


def to_data(value: Value) -> JsonValue:
    result: dict[str, JsonValue] = {}
    for name, field in type(value).model_fields.items():
        item = getattr(value, name)
        if (
            name in ("metadata", "extensions")
            and item in ({}, [])
            and name not in value.model_fields_set
        ):
            continue
        explicit_json = (
            isinstance(value, InputResolution)
            and name == "value"
            or isinstance(value, Result)
            and name in ("judgment", "output")
        ) and name in value.model_fields_set
        if item is None and not field.is_required() and not explicit_json:
            continue
        result[field.alias or name] = _data(item)
    return result


def _data(item: object) -> JsonValue:
    if isinstance(item, Value):
        return to_data(item)
    if isinstance(item, list):
        return [_data(v) for v in cast(list[object], item)]
    if isinstance(item, dict):
        return {k: _data(v) for k, v in cast(dict[str, object], item).items()}
    return cast(JsonValue, item)


def serialize(value: Value) -> str:
    return json.dumps(
        to_data(value), ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def _pairs(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("PROTOCOL_JSON", "Duplicate mapping key", details=key)
        result[key] = value
    return result


def _constant(value: str) -> JsonValue:
    raise ProtocolError("PROTOCOL_JSON", "Nonfinite JSON number", details=value)


def decode(value: str | bytes | JsonValue) -> JsonValue:
    if isinstance(value, (str, bytes)):
        try:
            raw = value.decode("utf-8") if isinstance(value, bytes) else value
            parsed = cast(
                JsonValue, json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
            )
        except (ValueError, UnicodeError) as exc:
            if isinstance(exc, ProtocolError):
                raise
            raise ProtocolError("PROTOCOL_JSON", "Invalid UTF-8 JSON") from exc
    else:
        parsed = value
    _json_value(parsed)
    return parsed


def _json_value(value: object) -> None:
    import math

    # StrEnum is a transparent JSON string representation, including the SDK's
    # typed error codes. Do not broaden numeric/boolean coercion or other enums.
    if value is None or type(value) in (str, bool, int) or isinstance(value, StrEnum):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in cast(list[object], value):
            _json_value(item)
        return
    if type(value) is dict:
        for key, item in cast(dict[object, object], value).items():
            if not isinstance(key, str):
                raise ProtocolError("PROTOCOL_JSON", "JSON mapping keys must be strings")
            _json_value(item)
        return
    raise ProtocolError("PROTOCOL_JSON", "Non-JSON or nonfinite value")
