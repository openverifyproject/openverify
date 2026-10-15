"""Shared standard-provider wire shapes and structured findings."""

from collections.abc import Awaitable, Callable
from typing import cast

from pydantic import JsonValue

from openverify.model import Context, Evidence, ExecutionObservation, JsonSchema, Result
from openverify.relay.providers import FunctionProvider, OperationKind, provider

STRING: JsonSchema = {"type": "string"}
STRINGS: JsonSchema = {"type": "array", "items": {"type": "string"}}
OBJECT: JsonSchema = {"type": "object"}
ARRAY: JsonSchema = {"type": "array"}


def object_schema(
    properties: dict[str, JsonSchema], *, optional: set[str] | None = None
) -> JsonSchema:
    return {
        "type": "object",
        "properties": cast(JsonValue, properties),
        "required": [n for n in properties if n not in (optional or set())],
        "additionalProperties": False,
    }


def judge(findings: list[JsonValue], *, observations: JsonValue = None) -> Result:
    return Result(
        disposition="EXECUTED",
        execution_outcome="SUCCESS",
        applicability="APPLICABLE",
        determination="KNOWN",
        verdict="FAIL" if findings else "PASS",
        output={"findings": findings, "observations": observations},
        evidence=[Evidence(structured_data=f) for f in findings],
    )


def standard(
    name: str,
    kind: OperationKind,
    inputs: dict[str, JsonSchema],
    outputs: dict[str, JsonSchema],
    function: Callable[[Context, Context], Awaitable[Context | Result | ExecutionObservation]],
    *,
    config: JsonSchema | None = None,
    optional_inputs: set[str] | None = None,
) -> FunctionProvider:
    if kind in ("EVALUATE", "AGGREGATE"):
        inputs = {**inputs, "subject": OBJECT, "criterion": OBJECT}
        outputs = {**outputs, "result": OBJECT}
    if kind == "CONTROL":
        outputs = {**outputs, "decision": OBJECT}
    return provider(
        provider_id=f"openverify.standard.{name}",
        capability_id=f"openverify.{name}",
        kind=kind,
        input_schema=object_schema(inputs, optional=optional_inputs),
        output_schema=object_schema(outputs),
        config_schema=config if config is not None else object_schema({}),
    )(function)
