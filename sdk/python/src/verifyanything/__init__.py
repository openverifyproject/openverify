"""Standalone wire SDK, independent of Relay; preserves the existing Python package."""

import json
import math
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

__version__ = "0.1.0"
VCP_VERSION = "draft"
PROVIDER_CONTRACT_VERSION = "0.1"
SPEC_REVISION = "5f17f402a270882f244a54dde25eda92a085eb39"
_bundle = json.loads(files(__package__).joinpath("bundle.json").read_text(encoding="utf-8"))
_registry = Registry().with_resources(
    (key, Resource.from_contents(value)) for key, value in _bundle["schemas"].items()
)


class ProtocolError(ValueError):
    """Stable protocol diagnostic; SDK_UNSUPPORTED is explicitly local."""

    def __init__(self, code: str, message: str = "", path: str = ""):
        super().__init__(message or code)
        self.code, self.message, self.path = code, message or code, path


@dataclass(frozen=True)
class WireObject:
    """JSON object preserving presence, explicit payload null and extensions."""

    data: dict[str, Any]


def _check(schema: Any, value: Any, code: str) -> None:
    try:
        error = next(Draft202012Validator(schema, registry=_registry).iter_errors(value), None)
    except Exception as exc:
        raise ProtocolError("INVALID_PROVIDER_OUTPUT", str(exc)) from exc
    if error:
        raise ProtocolError(
            code,
            error.message,
            "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in error.path),
        )


def validate_structure(contract: str, kind: str, value: Any) -> None:
    """Validate wire structure only; no semantic or execution support claim."""
    prefix = {"vcp": "urn:verification:draft:", "provider": "urn:openverify:provider:0.1:"}.get(
        contract
    )
    if not prefix or prefix + kind not in _bundle["schemas"]:
        raise ProtocolError("SDK_UNSUPPORTED")
    if (
        contract == "vcp"
        and isinstance(value, dict)
        and "protocol" in value
        and value["protocol"] != "draft"
    ):
        raise ProtocolError("PROTOCOL_VERSION")
    if (
        contract == "provider"
        and kind == "invocation"
        and isinstance(value, dict)
        and "contract_version" in value
        and value["contract_version"] != "0.1"
    ):
        raise ProtocolError("CONTRACT_VERSION_UNSUPPORTED")
    _check(
        _bundle["schemas"][prefix + kind],
        value,
        "PROTOCOL_STRUCTURE"
        if contract == "vcp"
        else "INVALID_INVOCATION"
        if kind == "invocation"
        else "INVALID_PROVIDER_OUTPUT",
    )


def validate_data(schema: Any, value: Any, code: str = "INVALID_INPUT") -> None:
    """Validate self-contained Draft 2020-12 capability data; format is annotation."""
    positions: set[str] = set()
    refs = []

    def visit(s: Any, path: str = "", top: bool = True) -> None:
        positions.add(path)
        if isinstance(s, bool):
            return
        if (
            not isinstance(s, dict)
            or (not top and "$id" in s)
            or any(k in s for k in ("$anchor", "$dynamicAnchor", "$dynamicRef"))
        ):
            raise ProtocolError("INVALID_PROVIDER_OUTPUT")
        if "$schema" in s and s["$schema"] != "https://json-schema.org/draft/2020-12/schema":
            raise ProtocolError("INVALID_PROVIDER_OUTPUT")
        if "$ref" in s:
            r = s["$ref"]
            if not isinstance(r, str) or (r != "#" and not r.startswith("#/")):
                raise ProtocolError("INVALID_PROVIDER_OUTPUT")
            refs.append(r[1:])
        for key in ("properties", "patternProperties", "$defs", "dependentSchemas"):
            if isinstance(s.get(key), dict):
                for name, child in s[key].items():
                    visit(
                        child,
                        path + "/" + key + "/" + name.replace("~", "~0").replace("/", "~1"),
                        False,
                    )
        for key in (
            "additionalProperties",
            "unevaluatedProperties",
            "propertyNames",
            "contains",
            "items",
            "unevaluatedItems",
            "not",
            "if",
            "then",
            "else",
            "contentSchema",
        ):
            if key in s:
                visit(s[key], path + "/" + key, False)
        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            if isinstance(s.get(key), list):
                for i, child in enumerate(s[key]):
                    visit(child, path + "/" + key + "/" + str(i), False)

    visit(schema)
    if not all(r in positions for r in refs):
        raise ProtocolError("INVALID_PROVIDER_OUTPUT")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise ProtocolError("INVALID_PROVIDER_OUTPUT", str(exc)) from exc
    _check(schema, value, code)


def validate(contract: str, kind: str, value: Any) -> WireObject:
    """Validate documented standalone semantics; unsupported types fail closed."""
    validate_structure(contract, kind, value)
    if contract == "vcp" and kind not in _bundle["semantic_vcp_types"]:
        raise ProtocolError("SDK_UNSUPPORTED")
    for rule in _bundle["rules"].get(kind, []):
        _check(
            rule["schema"],
            value,
            "INVALID_PROVIDER_OUTPUT" if contract == "provider" else rule["code"],
        )
    if kind == "resource" and value["kind"] == "RANGE" and value["minimum"] > value["maximum"]:
        raise ProtocolError("RESOURCE_MEASUREMENT")
    if contract == "vcp":
        for key, target in (("extensions", "extension"), ("evidence", "evidence")):
            for item in value.get(key, []):
                validate("vcp", target, item)
        if value.get("artifact_ref") is not None:
            validate("vcp", "artifact-ref", value["artifact_ref"])
        for item in value.get("usage", {}).values():
            validate("vcp", "resource", item)
    else:
        if "deadline" in value or "timestamp" in value:
            raise ProtocolError("SDK_UNSUPPORTED", "Timestamp semantics are not implemented")
        if kind == "provider-event":
            target = {"evidence": "evidence", "artifact": "artifact-ref"}.get(value["kind"])
            try:
                if target:
                    validate("vcp", target, value["payload"])
                if value["kind"] == "resource_usage":
                    for measurement in value["payload"].values():
                        validate("vcp", "resource", measurement)
            except ProtocolError as exc:
                raise ProtocolError("INVALID_PROVIDER_OUTPUT") from exc
        if kind == "provider-manifest":
            seen = set()
            for cap in value["capabilities"]:
                pair = cap["capability_id"], cap["capability_version"]
                if pair in seen or (
                    "vcp_version" in cap
                    and cap["vcp_version"] not in value["supported_vcp_versions"]
                ):
                    raise ProtocolError("INVALID_PROVIDER_OUTPUT")
                seen.add(pair)
                validate("provider", "capability", cap)
        if kind == "capability":
            for key in ("input_schema", "config_schema", "output_schema"):
                try:
                    validate_data(value[key], None)
                except ProtocolError as exc:
                    if exc.code != "INVALID_INPUT":
                        raise
        if kind == "initialize-result":
            validate("provider", "provider-manifest", value["manifest"])
        if "vcp_version" in value and value["vcp_version"] != "draft":
            raise ProtocolError(
                "INVALID_INVOCATION" if kind == "invocation" else "INVALID_PROVIDER_OUTPUT"
            )
        for key in ("resource_budget", "resource_usage"):
            for resource in value.get(key, {}).values():
                try:
                    validate("vcp", "resource", resource)
                except ProtocolError as exc:
                    raise ProtocolError(
                        "INVALID_INVOCATION" if kind == "invocation" else "INVALID_PROVIDER_OUTPUT"
                    ) from exc
                if key == "resource_budget" and (
                    resource["kind"] != "EXACT" or value.get("vcp_version") != "draft"
                ):
                    raise ProtocolError("INVALID_INVOCATION")
    return WireObject(value)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def _nonfinite(text: str) -> Any:
    raise ValueError("Nonfinite JSON number")


def _float(text: str) -> float:
    from decimal import Decimal

    value = float(text)
    if not math.isfinite(value) or Decimal(str(value)) != Decimal(text):
        raise ValueError("JSON number cannot be represented faithfully")
    return value


def parse(contract: str, kind: str, text: str | bytes) -> WireObject:
    try:
        value = json.loads(
            text, object_pairs_hook=_pairs, parse_constant=_nonfinite, parse_float=_float
        )
    except (ValueError, UnicodeError) as exc:
        raise ProtocolError(
            "PROTOCOL_JSON"
            if contract == "vcp"
            else "INVALID_INVOCATION"
            if kind == "invocation"
            else "INVALID_PROVIDER_OUTPUT",
            str(exc),
        ) from exc
    return validate(contract, kind, value)


def serialize(value: WireObject) -> str:
    return json.dumps(value.data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
