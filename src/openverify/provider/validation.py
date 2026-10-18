"""Offline structural and semantic Provider Contract validation."""

import json
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from importlib.resources import files
from typing import NamedTuple, cast
from urllib.parse import unquote

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError as InvalidSchema
from jsonschema.exceptions import ValidationError as SchemaError
from pydantic import JsonValue, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import Schema

from openverify.errors import ProtocolError
from openverify.provider_codes import ProviderErrorCode
from openverify.serialization import decode
from openverify.validation import ValidatorPort
from openverify.validation import parse_object as parse_vcp

from .model import (
    CancelRequest,
    Capability,
    InitializeRequest,
    InitializeResult,
    Invocation,
    Outcome,
    ProviderError,
    ProviderEvent,
    ProviderManifest,
    ProviderValue,
)

TYPES: dict[str, type[ProviderValue]] = {
    "provider-manifest": ProviderManifest,
    "capability": Capability,
    "invocation": Invocation,
    "provider-event": ProviderEvent,
    "cancel-request": CancelRequest,
    "outcome": Outcome,
    "provider-error": ProviderError,
    "initialize-request": InitializeRequest,
    "initialize-result": InitializeResult,
}


class ProviderContractError(ValueError):
    def __init__(self, code: str, message: str, details: JsonValue = None):
        code = str.__str__(code)
        super().__init__(f"{code}: {message}")
        try:
            self.code: ProviderErrorCode | str = ProviderErrorCode(str.__str__(code))
        except ValueError:
            self.code = code
        self.message = message
        self.details = details

    def as_dict(self) -> dict[str, JsonValue]:
        return {"code": str.__str__(self.code), "message": self.message, "details": self.details}


def fail(code: str, message: str) -> None:
    raise ProviderContractError(code, message)


def wire_data(value: ProviderValue) -> dict[str, JsonValue]:
    # Preserve explicitly supplied null JSON payloads and unknown extension values.
    return cast(dict[str, JsonValue], value.model_dump(mode="json", exclude_unset=True))


def serialize(value: ProviderValue) -> str:
    return json.dumps(wire_data(value), ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def load_provider_schema(name: str) -> dict[str, JsonValue]:
    if name not in TYPES:
        fail("PROTOCOL_VIOLATION", "Unknown Provider Contract schema")
    return cast(
        dict[str, JsonValue],
        json.loads(
            files("openverify.provider")
            .joinpath(f"data/schemas/{name}.schema.json")
            .read_text(encoding="utf-8")
        ),
    )


class Instant(NamedTuple):
    second: datetime
    fraction: Decimal


def timestamp(value: str) -> Instant:
    try:
        match = re.fullmatch(
            r"([0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2})"
            r"(\.[0-9]+)?([Zz]|\+00:00)",
            value,
        )
        if match is None:
            raise ValueError("UTC RFC3339 required")
        parsed = datetime.fromisoformat((match[1] + match[3]).upper())
        if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
            raise ValueError("UTC required")
        return Instant(parsed, Decimal(match[2] or "0"))
    except ValueError as exc:
        raise ProviderContractError("PROTOCOL_VIOLATION", "Invalid UTC timestamp") from exc


def _date_time(value: object) -> bool:
    if not isinstance(value, str):
        return True
    try:
        timestamp(value)
        return True
    except ProviderContractError:
        return False


@lru_cache
def _validator(name: str) -> Draft202012Validator:
    resources: list[tuple[str, Resource[Schema]]] = []
    for package, directory in (
        ("openverify", "data/schemas"),
        ("openverify.provider", "data/schemas"),
    ):
        for path in files(package).joinpath(directory).iterdir():
            schema = cast(dict[str, JsonValue], json.loads(path.read_text(encoding="utf-8")))
            resources.append(
                (cast(str, schema["$id"]), Resource.from_contents(cast(Schema, schema)))
            )
    checker = FormatChecker()
    checker.checks("date-time")(_date_time)
    return Draft202012Validator(
        load_provider_schema(name),
        registry=Registry[Schema]().with_resources(resources),
        format_checker=checker,
    )


def _code(name: str) -> str:
    if name == "invocation":
        return "INVALID_INVOCATION"
    if name in ("cancel-request", "initialize-request"):
        return "PROTOCOL_VIOLATION"
    return "INVALID_PROVIDER_OUTPUT"


def parse_provider_object(name: str, data: str | bytes | JsonValue) -> ProviderValue:
    code = _code(name)
    if name not in TYPES:
        fail("PROTOCOL_VIOLATION", "Unknown Provider Contract object")
    try:
        raw = decode(data)
    except ProtocolError as exc:
        raise ProviderContractError(code, "Invalid UTF-8 JSON", exc.details) from exc
    if isinstance(raw, dict) and "contract_version" in raw and raw["contract_version"] != "0.1":
        fail("CONTRACT_VERSION_UNSUPPORTED", "Unsupported contract version")
    try:
        cast(ValidatorPort, _validator(name)).validate(raw)
        value = TYPES[name].model_validate(raw)
    except (SchemaError, ValidationError) as exc:
        raise ProviderContractError(code, "Wire object violates schema", str(exc)) from exc
    if isinstance(value, Capability):
        _capability(value)
    elif isinstance(value, ProviderManifest):
        identities = [(c.capability_id, c.capability_version) for c in value.capabilities]
        if len(identities) != len(set(identities)):
            fail(code, "Duplicate capability identity")
        for capability in value.capabilities:
            _capability(capability)
            if (
                capability.vcp_version is not None
                and capability.vcp_version not in value.supported_vcp_versions
            ):
                fail(code, "Capability VCP version is not advertised")
    elif isinstance(value, InitializeResult):
        validate_provider_manifest(value.manifest)
        if value.contract_version not in value.manifest.supported_contract_versions:
            fail(code, "Selected version not supported by manifest")
    elif isinstance(value, Invocation):
        if value.vcp_version is not None and value.vcp_version != "draft":
            fail(code, "Unsupported VCP interchange version")
        if value.resource_budget is not None:
            _vector(value.resource_budget, code)
            if value.vcp_version != "draft" or any(
                not isinstance(m, dict) or m.get("kind") != "EXACT"
                for m in value.resource_budget.values()
            ):
                fail(code, "Budget requires VCP draft and EXACT upper limits")
    elif isinstance(value, ProviderEvent):
        if value.kind in ("evidence", "artifact"):
            _vcp("evidence" if value.kind == "evidence" else "artifact-ref", value.payload, code)
        elif value.kind == "resource_usage":
            _vector(value.payload, code)
    elif isinstance(value, Outcome) and value.resource_usage is not None:
        _vector(value.resource_usage, code)
    return value


def _vcp(name: str, value: JsonValue, code: str) -> None:
    try:
        parse_vcp(name, value)
    except ProtocolError as exc:
        raise ProviderContractError(code, "Invalid embedded VCP object", exc.as_dict()) from exc


def _vector(value: JsonValue, code: str) -> None:
    if not isinstance(value, dict):
        fail(code, "ResourceVector must be a mapping")
    assert isinstance(value, dict)
    for measurement in value.values():
        _vcp("resource", measurement, code)


def _schema_nodes(value: dict[str, JsonValue] | bool) -> Iterator[dict[str, JsonValue] | bool]:
    """Visit schema positions, never annotations/default instance values."""
    yield value
    if isinstance(value, bool):
        return
    for keyword in ("properties", "patternProperties", "$defs", "dependentSchemas"):
        children = value.get(keyword)
        if isinstance(children, dict):
            for child in children.values():
                if isinstance(child, (dict, bool)):
                    yield from _schema_nodes(child)
    for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
        children = value.get(keyword)
        if isinstance(children, list):
            for child in children:
                if isinstance(child, (dict, bool)):
                    yield from _schema_nodes(child)
    for keyword in (
        "not",
        "if",
        "then",
        "else",
        "items",
        "contains",
        "additionalProperties",
        "unevaluatedProperties",
        "unevaluatedItems",
        "propertyNames",
        "contentSchema",
    ):
        child = value.get(keyword)
        if isinstance(child, (dict, bool)):
            yield from _schema_nodes(child)


def _capability(capability: Capability) -> None:
    for schema in (capability.input_schema, capability.config_schema, capability.output_schema):
        try:
            Draft202012Validator.check_schema(schema)
            nodes = list(_schema_nodes(schema))
            for node in nodes:
                if isinstance(node, dict):
                    reference = node.get("$ref")
                    if (
                        reference is not None
                        and (
                            not isinstance(reference, str)
                            or not (reference == "#" or reference.startswith("#/"))
                        )
                    ) or any(key in node for key in ("$dynamicRef", "$dynamicAnchor", "$anchor")):
                        fail(
                            "INVALID_PROVIDER_OUTPUT",
                            "Capability schemas require local JSON Pointer references",
                        )
                    if node is not schema and "$id" in node:
                        fail(
                            "INVALID_PROVIDER_OUTPUT", "Nested schema resource IDs are unsupported"
                        )
                    if isinstance(reference, str):
                        target: JsonValue = schema
                        for token in unquote(reference[2:]).split("/") if reference != "#" else []:
                            if re.search(r"~(?:[^01]|$)", token):
                                fail("INVALID_PROVIDER_OUTPUT", "Invalid JSON Pointer escape")
                            token = token.replace("~1", "/").replace("~0", "~")
                            if isinstance(target, dict) and token in target:
                                target = target[token]
                            elif (
                                isinstance(target, list)
                                and re.fullmatch(r"0|[1-9][0-9]*", token)
                                and int(token) < len(target)
                            ):
                                target = cast(list[JsonValue], target)[int(token)]
                            else:
                                fail(
                                    "INVALID_PROVIDER_OUTPUT",
                                    "Unresolved capability schema reference",
                                )
                        if not isinstance(target, (dict, bool)):
                            fail(
                                "INVALID_PROVIDER_OUTPUT",
                                "Schema reference does not target a schema",
                            )
                        if isinstance(target, dict) and not any(
                            target is candidate for candidate in nodes
                        ):
                            fail(
                                "INVALID_PROVIDER_OUTPUT",
                                "Reference target is outside supported schema positions",
                            )
                    if (
                        "$schema" in node
                        and node["$schema"] != "https://json-schema.org/draft/2020-12/schema"
                    ):
                        fail(
                            "INVALID_PROVIDER_OUTPUT",
                            "Capability schema dialect must be Draft 2020-12",
                        )
        except InvalidSchema as exc:
            raise ProviderContractError(
                "INVALID_PROVIDER_OUTPUT", "Invalid capability schema"
            ) from exc


def validate_payload(schema: dict[str, JsonValue] | bool, value: JsonValue, code: str) -> None:
    try:
        cast(ValidatorPort, Draft202012Validator(schema, registry=Registry())).validate(value)
    except Exception as exc:
        raise ProviderContractError(
            code, "Value violates declared capability schema", str(exc)
        ) from exc


def parse_provider_manifest(data: str | bytes | JsonValue) -> ProviderManifest:
    return cast(ProviderManifest, parse_provider_object("provider-manifest", data))


def parse_invocation(data: str | bytes | JsonValue) -> Invocation:
    return cast(Invocation, parse_provider_object("invocation", data))


def parse_provider_event(data: str | bytes | JsonValue) -> ProviderEvent:
    return cast(ProviderEvent, parse_provider_object("provider-event", data))


def parse_outcome(data: str | bytes | JsonValue) -> Outcome:
    return cast(Outcome, parse_provider_object("outcome", data))


def parse_cancel_request(data: str | bytes | JsonValue) -> CancelRequest:
    return cast(CancelRequest, parse_provider_object("cancel-request", data))


def validate_provider_manifest(value: ProviderManifest) -> None:
    parse_provider_manifest(wire_data(value))


def validate_invocation(value: Invocation) -> None:
    parse_invocation(wire_data(value))


def validate_provider_event(value: ProviderEvent) -> None:
    parse_provider_event(wire_data(value))


def validate_outcome(value: Outcome) -> None:
    parse_outcome(wire_data(value))
