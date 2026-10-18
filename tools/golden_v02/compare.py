"""Strict JSON equality and explicit, path-scoped nondeterminism assertions."""

from __future__ import annotations

import math
from typing import Any


class Difference(AssertionError):
    pass


def json_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise Difference("nonfinite JSON number")
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        return "object"
    raise Difference(f"not JSON: {type(value).__name__}")


def equal(expected: Any, observed: Any, path: str = "") -> None:
    ek, ok = json_kind(expected), json_kind(observed)
    if ek != ok:
        raise Difference(f"{path}: JSON type {ek} != {ok}")
    if ek == "object":
        if expected.keys() != observed.keys():
            raise Difference(
                f"{path}: keys expected={sorted(expected)} observed={sorted(observed)}"
            )
        for key in expected:
            equal(
                expected[key], observed[key], path + "/" + key.replace("~", "~0").replace("/", "~1")
            )
    elif ek == "array":
        if len(expected) != len(observed):
            raise Difference(f"{path}: array lengths {len(expected)} != {len(observed)}")
        for i, (a, b) in enumerate(zip(expected, observed)):
            equal(a, b, f"{path}/{i}")
    elif expected != observed:
        raise Difference(f"{path}: expected {expected!r}, observed {observed!r}")


def same(a: Any, b: Any) -> bool:
    try:
        equal(a, b)
        return True
    except Difference:
        return False


def utc(value: str):
    if not value.endswith(("Z", "z", "+00:00")):
        raise Difference(f"not UTC: {value}")
    from tools.golden_v02.provider_oracle import instant

    return instant(value)


def fields(expected: dict, observed: dict, path: str = "") -> None:
    """Explicit field assertion; callers must separately validate the whole record."""
    for key, value in expected.items():
        if key not in observed:
            raise Difference(f"{path}/{key}: missing")
        equal(value, observed[key], path + "/" + key)
