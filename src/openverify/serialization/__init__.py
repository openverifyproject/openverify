"""Strict JSON interchange, without claiming canonical cross-language bytes."""

import json
from typing import cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.model import Value


def to_data(value: Value) -> JsonValue:
    result: dict[str, JsonValue] = {}
    for name, field in type(value).model_fields.items():
        item = getattr(value, name)
        if item is None and not field.is_required():
            continue
        result[name] = _data(item)
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

    if value is None or type(value) in (str, bool, int):
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
