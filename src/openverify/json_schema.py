"""Domain-neutral offline schemas; no provider resolution or network fetching."""

import re
from collections.abc import Iterator
from typing import Protocol, cast
from urllib.parse import unquote

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError as InvalidSchema
from pydantic import JsonValue
from referencing import Registry

from openverify.errors import ProtocolError
from openverify.model import JsonSchema


def _fail(code: str, message: str) -> None:
    raise ProtocolError(code, message)


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


def check_schema(schema: JsonSchema) -> None:
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
                    _fail(
                        "SCHEMA_UNSUPPORTED",
                        "Capability schemas require local JSON Pointer references",
                    )
                if node is not schema and "$id" in node:
                    _fail("SCHEMA_UNSUPPORTED", "Nested schema resource IDs are unsupported")
                if isinstance(reference, str):
                    target: JsonValue = schema
                    for token in unquote(reference[2:]).split("/") if reference != "#" else []:
                        if re.search(r"~(?:[^01]|$)", token):
                            _fail("SCHEMA_UNSUPPORTED", "Invalid JSON Pointer escape")
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
                            _fail(
                                "SCHEMA_UNSUPPORTED",
                                "Unresolved capability schema reference",
                            )
                    if not isinstance(target, (dict, bool)):
                        _fail(
                            "SCHEMA_UNSUPPORTED",
                            "Schema reference does not target a schema",
                        )
                    if isinstance(target, dict) and not any(
                        target is candidate for candidate in nodes
                    ):
                        _fail(
                            "SCHEMA_UNSUPPORTED",
                            "Reference target is outside supported schema positions",
                        )
                if (
                    "$schema" in node
                    and node["$schema"] != "https://json-schema.org/draft/2020-12/schema"
                ):
                    _fail(
                        "SCHEMA_UNSUPPORTED",
                        "Capability schema dialect must be Draft 2020-12",
                    )
    except InvalidSchema as exc:
        raise ProtocolError("SCHEMA_UNSUPPORTED", "Invalid capability schema") from exc


class Validator(Protocol):
    def validate(self, instance: JsonValue) -> None: ...


def validate_value(schema: JsonSchema, value: JsonValue, code: str = "DATAFLOW_VALUE") -> None:
    try:
        cast(Validator, Draft202012Validator(schema, registry=Registry())).validate(value)
    except Exception as exc:
        raise ProtocolError(code, "Value violates declared schema", details=str(exc)) from exc


def obvious_incompatible(source: JsonSchema, target: JsonSchema) -> bool:
    if source is False or target is False:
        return True
    if source is True or target is True:
        return False

    def types(schema: dict[str, JsonValue]) -> set[str]:
        value = schema.get("type")
        result = {value} if isinstance(value, str) else set(cast(list[str], value or []))
        if "number" in result:
            result.add("integer")
        return result

    left, right = types(source), types(target)
    if left and right and not left & right:
        return True
    # A finite source can be checked exactly; no claim of general subsumption.
    finite = [source["const"]] if "const" in source else source.get("enum")
    if isinstance(finite, list):
        for value in finite:
            try:
                validate_value(target, value)
                return False
            except ProtocolError:
                pass
        return True
    return False
